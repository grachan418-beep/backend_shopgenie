from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from products.models import Product
from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "line_total"]
        read_only_fields = ["id", "product_name", "unit_price", "line_total"]


class InvoiceCreateSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128, required=True)
    items = serializers.ListField(
        child=serializers.DictField(), allow_empty=False, required=True
    )

    def validate_items(self, value):
        seen_products = set()
        for item in value:
            product_id = item.get("product")
            quantity = item.get("quantity")
            if product_id is None:
                raise serializers.ValidationError("product is required for each item")
            if quantity is None:
                raise serializers.ValidationError("quantity is required for each item")
            try:
                quantity = Decimal(str(quantity))
            except (InvalidOperation, ValueError, TypeError):
                raise serializers.ValidationError({"quantity": "Invalid quantity"})
            if quantity <= 0:
                raise serializers.ValidationError({"quantity": "Quantity must be positive"})
            if product_id in seen_products:
                raise serializers.ValidationError({"items": "Duplicate product in invoice"})
            seen_products.add(product_id)
        return value
