from decimal import Decimal, InvalidOperation
from rest_framework import serializers


class FlutterInvoiceItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.CharField(required=True)
    unit_price = serializers.CharField(required=False, allow_blank=True, default="0")


class FlutterInvoiceSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128, required=True)
    payment_mode = serializers.CharField(required=False, allow_blank=True, default="")
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    items = serializers.ListField(child=FlutterInvoiceItemSerializer(), allow_empty=False, required=True)

    def validate_items(self, value):
        seen_products = set()
        for item in value:
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            if product_id is None:
                raise serializers.ValidationError("product_id is required for each item")
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
