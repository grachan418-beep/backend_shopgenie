from django.db import IntegrityError, transaction
from django.db.models import F
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
import hashlib, json
from .models import Invoice, InvoiceItem
from .serializers import InvoiceCreateSerializer, InvoiceItemSerializer
from products.models import Product
from inventory.models import StockAdjustment


def user_effective_shop(user):
    if user.is_owner and getattr(user, "owned_shop", None):
        return user.owned_shop
    if user.is_worker and user.is_worker_active and user.assigned_shop_id:
        return user.assigned_shop
    return None


class IsShopMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        shop = user_effective_shop(request.user)
        if shop is None:
            return False
        return obj.shop_id == shop.id


class InvoiceViewSet(viewsets.ViewSet):
    permission_classes = [IsShopMember]

    def _require_billing_permission(self, request):
        user = request.user
        if user.is_owner:
            return
        if user.is_worker and user.is_worker_active and user.can_confirm_bills:
            return
        raise PermissionDenied("Worker is not authorized to create invoices")

    def list(self, request):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        if request.user.is_worker and not request.user.can_view_invoices:
            raise PermissionDenied("Worker cannot view invoices")
        invoices = Invoice.objects.filter(shop=shop).order_by("-created_at")
        data = [
            {
                "id": inv.id,
                "idempotency_key": inv.idempotency_key,
                "total_amount": str(inv.total_amount),
                "status": inv.status,
                "created_at": inv.created_at,
            }
            for inv in invoices
        ]
        return Response(data)

    def retrieve(self, request, pk=None):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        try:
            inv = Invoice.objects.get(pk=pk, shop=shop)
        except Invoice.DoesNotExist:
            raise ValidationError({"detail": "Invoice not found"})
        items = InvoiceItemSerializer(inv.items.all(), many=True).data
        return Response(
            {
                "id": inv.id,
                "shop": inv.shop_id,
                "idempotency_key": inv.idempotency_key,
                "total_amount": str(inv.total_amount),
                "status": inv.status,
                "created_at": inv.created_at,
                "items": items,
            }
        )

    def create(self, request):
        self._require_billing_permission(request)
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")

        serializer = InvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["idempotency_key"]
        raw_items = serializer.validated_data["items"]

        # Canonical signature for idempotency payload comparison
        canonical = sorted(
            (int(item["product"]), str(Decimal(str(item["quantity"]))))
            for item in raw_items
        )
        signature = hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()

        product_ids = [item["product"] for item in raw_items]

        with transaction.atomic():
            # Reserve the invoice row via the unique (shop, idempotency_key)
            # constraint inside a nested atomic block so a duplicate-key failure
            # is rolled back cleanly without aborting the outer transaction.
            inv = None
            try:
                with transaction.atomic():
                    inv = Invoice.objects.create(
                        shop=shop,
                        created_by=request.user,
                        idempotency_key=key,
                        request_signature=signature,
                        total_amount=Decimal("0"),
                        status=Invoice.Status.COMPLETED,
                    )
            except IntegrityError:
                existing = (
                    Invoice.objects.filter(shop=shop, idempotency_key=key)
                    .select_for_update()
                    .first()
                )
                if existing is None:
                    raise ValidationError({"idempotency_key": "Duplicate invoice key"})
                if existing.request_signature != signature:
                    return Response(
                        {
                            "detail": "Idempotency key reused with a different request payload",
                            "id": existing.id,
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                items = InvoiceItemSerializer(existing.items.all(), many=True).data
                return Response(
                    {
                        "id": existing.id,
                        "shop": existing.shop_id,
                        "idempotency_key": existing.idempotency_key,
                        "total_amount": str(existing.total_amount),
                        "status": existing.status,
                        "created_at": existing.created_at,
                        "items": items,
                    },
                    status=status.HTTP_200_OK,
                )

            # We own this invoice row; validate and deduct stock in the same
            # transaction so stock deduction and invoice creation are atomic.
            locked = Product.objects.select_for_update().filter(
                id__in=product_ids
            ).order_by("id")
            products = {p.id: p for p in locked}
            if len(products) != len(product_ids):
                raise ValidationError({"items": "One or more products not found"})

            total = Decimal("0")
            invoice_items = []
            adjustments = []
            for item in raw_items:
                product = products[item["product"]]
                if product.shop_id != shop.id:
                    raise ValidationError({"items": f"Product {product.id} does not belong to this shop"})
                if product.status != Product.Status.PUBLISHED:
                    raise ValidationError({"items": f"Product {product.id} is not available"})
                quantity = Decimal(str(item["quantity"]))
                if product.stock_quantity < quantity:
                    raise ValidationError({"items": f"Insufficient stock for {product.name}"})
                unit_price = product.selling_price
                line_total = unit_price * quantity
                total += line_total
                invoice_items.append(
                    InvoiceItem(
                        invoice=inv,
                        product=product,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        line_total=line_total,
                    )
                )
                adjustments.append(
                    StockAdjustment(
                        product=product,
                        actor=request.user,
                        delta=-quantity,
                        reason=StockAdjustment.Reason.OTHER,
                        note=f"Invoice sale {key}",
                    )
                )
                product.stock_quantity = F("stock_quantity") - quantity
                product.save(update_fields=["stock_quantity", "updated_at"])

            inv.total_amount = total
            inv.save(update_fields=["total_amount"])
            InvoiceItem.objects.bulk_create(invoice_items)
            StockAdjustment.objects.bulk_create(adjustments)

        # Refresh to read committed stock values
        inv.refresh_from_db()
        data = InvoiceItemSerializer(inv.items.all(), many=True).data
        return Response(
            {
                "id": inv.id,
                "shop": inv.shop_id,
                "idempotency_key": inv.idempotency_key,
                "total_amount": str(inv.total_amount),
                "status": inv.status,
                "created_at": inv.created_at,
                "items": data,
            },
            status=status.HTTP_201_CREATED,
        )
