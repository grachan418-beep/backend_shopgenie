from django.db import models
from accounts.models import Shop, CustomUser
from products.models import Product


class Invoice(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="invoices")
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="created_invoices")
    idempotency_key = models.CharField(max_length=128)
    request_signature = models.CharField(max_length=128, blank=True, default="")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shopgenie_invoices"
        unique_together = ("shop", "idempotency_key")

    def __str__(self):
        return f"Invoice {self.id} ({self.shop_id})"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice_items")
    product_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "shopgenie_invoice_items"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
