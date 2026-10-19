from django.urls import path
from .views import ShopViewSet

shop_list = ShopViewSet.as_view({"get": "list"})
shop_detail = ShopViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", shop_list, name="shop-list"),
    path("<int:pk>/", shop_detail, name="shop-detail"),
]
