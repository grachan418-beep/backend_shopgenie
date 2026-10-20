from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import Shop
from shops.serializers import ShopPublicSerializer, ShopOwnerSerializer


class IsShopOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_owner
        )


class IsPublicReadOrAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)


class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShopPublicSerializer
    permission_classes = [IsPublicReadOrAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "status"]
    search_fields = ["name", "category"]
    ordering_fields = ["name", "category", "created_at", "rating"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action == "my_shop":
            return [IsShopOwner()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        return Shop.objects.filter(status=Shop.Status.PUBLISHED)

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsShopOwner])
    def my_shop(self, request):
        shop = getattr(request.user, "owned_shop", None)
        if shop is None:
            return Response(
                {"detail": "No shop is associated with this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "GET":
            serializer = ShopOwnerSerializer(shop)
            return Response(serializer.data)

        # PATCH
        serializer = ShopOwnerSerializer(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
