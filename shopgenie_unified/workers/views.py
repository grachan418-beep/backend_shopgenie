from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts.models import CustomUser, Shop
from .serializers import WorkerSerializer, WorkerCreateSerializer


def user_effective_shop(user):
    if user.is_owner and getattr(user, "owned_shop", None):
        return user.owned_shop
    if user.is_worker and user.is_worker_active and user.assigned_shop_id:
        return user.assigned_shop
    return None


class IsShopOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_owner
        )


class WorkerViewSet(viewsets.ViewSet):
    permission_classes = [IsShopOwner]

    def list(self, request):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        workers = CustomUser.objects.filter(
            role=CustomUser.Role.SHOP_WORKER,
            assigned_shop=shop,
        ).order_by("-date_joined")
        return Response(WorkerSerializer(workers, many=True).data)

    def retrieve(self, request, pk=None):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        try:
            worker = CustomUser.objects.get(
                pk=pk, role=CustomUser.Role.SHOP_WORKER, assigned_shop=shop
            )
        except CustomUser.DoesNotExist:
            raise ValidationError({"detail": "Worker not found"})
        return Response(WorkerSerializer(worker).data)

    def create(self, request):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")

        serializer = WorkerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        worker = CustomUser.objects.create_user(
            email=validated["email"],
            username=validated["username"],
            password=validated["password"],
            first_name=validated.get("first_name", ""),
            last_name=validated.get("last_name", ""),
            role=CustomUser.Role.SHOP_WORKER,
            assigned_shop=shop,
            is_worker_active=validated.get("is_worker_active", True),
            can_view_invoices=validated.get("can_view_invoices", True),
            can_confirm_bills=validated.get("can_confirm_bills", True),
        )
        return Response(WorkerSerializer(worker).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        try:
            worker = CustomUser.objects.get(
                pk=pk, role=CustomUser.Role.SHOP_WORKER, assigned_shop=shop
            )
        except CustomUser.DoesNotExist:
            raise ValidationError({"detail": "Worker not found"})

        data = request.data
        allowed_fields = ["first_name", "last_name", "is_worker_active", "can_view_invoices", "can_confirm_bills"]
        for field in allowed_fields:
            if field in data:
                setattr(worker, field, data[field])
        worker.save()
        return Response(WorkerSerializer(worker).data)

    def destroy(self, request, pk=None):
        shop = user_effective_shop(request.user)
        if shop is None:
            raise PermissionDenied("No authorized shop")
        try:
            worker = CustomUser.objects.get(
                pk=pk, role=CustomUser.Role.SHOP_WORKER, assigned_shop=shop
            )
        except CustomUser.DoesNotExist:
            raise ValidationError({"detail": "Worker not found"})
        worker.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
