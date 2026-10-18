from django.urls import path
from .views import InvoiceViewSet

invoice_list = InvoiceViewSet.as_view({"get": "list", "post": "create"})
invoice_detail = InvoiceViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", invoice_list, name="invoice-list"),
    path("<int:pk>/", invoice_detail, name="invoice-detail"),
]
