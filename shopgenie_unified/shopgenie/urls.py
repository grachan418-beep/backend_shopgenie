from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/products/", include("products.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/invoices/", include("billing.urls")),
    path("api/shops/", include("shops.urls")),
]
