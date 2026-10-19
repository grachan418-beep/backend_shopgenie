from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from accounts.models import Shop
from shops.serializers import ShopPublicSerializer


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

    def get_queryset(self):
        return Shop.objects.filter(status=Shop.Status.PUBLISHED)
