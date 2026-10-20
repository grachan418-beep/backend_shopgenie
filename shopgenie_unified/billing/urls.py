from django.urls import path
from .views import InvoiceViewSet
from .flutter_views import FlutterInvoiceViewSet

invoice_list = InvoiceViewSet.as_view({"get": "list", "post": "create"})
invoice_detail = InvoiceViewSet.as_view({"get": "retrieve"})
flutter_invoice_create = FlutterInvoiceViewSet.as_view({"post": "create"})

urlpatterns = [
    path("", invoice_list, name="invoice-list"),
    path("<int:pk>/", invoice_detail, name="invoice-detail"),
    path("flutter/", flutter_invoice_create, name="flutter-invoice-create-alt"),
    path("invoices/", flutter_invoice_create, name="flutter-invoice-create"),
]
