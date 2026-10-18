from django.db import models
from products.models import Product
from accounts.models import CustomUser


class StockAdjustment(models.Model):
    class Reason(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        CORRECTION = "CORRECTION", "Correction"
        DAMAGE = "DAMAGE", "Damage"
        OTHER = "OTHER", "Other"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="adjustments")
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="stock_adjustments")
    delta = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shopgenie_stock_adjustments"
        ordering = ["-created_at"]
