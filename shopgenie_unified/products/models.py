from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Shop


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"
        KG = "KG", "Kilogram"
        GRAM = "GRAM", "Gram"
        LITER = "LITER", "Liter"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    category = models.CharField(max_length=100, default="General", db_index=True)
    description = models.TextField(blank=True, default="")
    mrp = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    image_url = models.URLField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shopgenie_products"

    def __str__(self):
        return f"{self.name} ({self.shop_id})"
