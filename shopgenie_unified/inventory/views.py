from django.db import transaction
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from .models import StockAdjustment
from .serializers import StockAdjustmentSerializer
from products.models import Product


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_owner or user.is_worker:
            shop = user.effective_shop
            if shop:
                return StockAdjustment.objects.filter(product__shop=shop)
        return StockAdjustment.objects.none()

    def perform_create(self, serializer):
        product = serializer.validated_data["product"]
        user = self.request.user
        shop = product.shop
        if not (user.is_owner and getattr(user, "owned_shop", None) == shop) and not (user.is_worker and user.assigned_shop_id == shop.id and user.is_worker_active):
            raise PermissionDenied()
        delta = serializer.validated_data["delta"]
        with transaction.atomic():
            p = Product.objects.select_for_update().get(pk=product.pk)
            new_stock = p.stock_quantity + delta
            if new_stock < 0:
                raise ValidationError({"delta": "Insufficient stock"})
            p.stock_quantity = new_stock
            p.save(update_fields=["stock_quantity", "updated_at"])
            serializer.save(actor=user)
