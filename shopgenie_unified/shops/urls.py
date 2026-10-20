from django.urls import path
from .views import ShopViewSet

shop_list = ShopViewSet.as_view({"get": "list"})
shop_detail = ShopViewSet.as_view({"get": "retrieve"})
shop_my_shop = ShopViewSet.as_view({"get": "my_shop", "patch": "my_shop"})

urlpatterns = [
    path("", shop_list, name="shop-list"),
    path("my_shop/", shop_my_shop, name="shop-my-shop"),
    path("<int:pk>/", shop_detail, name="shop-detail"),
]
