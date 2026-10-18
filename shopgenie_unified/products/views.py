from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Product
from .serializers import ProductPublicSerializer, ProductOwnerSerializer, ProductWriteSerializer


def is_owner_or_worker(user, shop):
    if user.is_owner and getattr(user, "owned_shop", None) == shop:
        return True
    if user.is_worker and user.assigned_shop_id == shop.id and user.is_worker_active:
        return True
    return False


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        user = self.request.user
        if user.is_authenticated and (user.is_owner or user.is_worker):
            return ProductOwnerSerializer
        return ProductPublicSerializer

    def get_queryset(self):
        qs = Product.objects.all()
        user = self.request.user
        if user.is_authenticated and (user.is_owner or user.is_worker):
            shop = user.effective_shop
            if shop:
                return qs.filter(shop=shop)
        return qs.filter(status=Product.Status.PUBLISHED)

    def perform_create(self, serializer):
        shop = serializer.validated_data["shop"]
        if not is_owner_or_worker(self.request.user, shop):
            raise PermissionDenied()
        serializer.save()

    def perform_update(self, serializer):
        if not is_owner_or_worker(self.request.user, serializer.instance.shop):
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if not is_owner_or_worker(self.request.user, instance.shop):
            raise PermissionDenied()
        instance.delete()
