from rest_framework import serializers
from .models import Product


class ProductPublicSerializer(serializers.ModelSerializer):
    store_id = serializers.CharField(source="shop.id", read_only=True)
    store_name = serializers.CharField(source="shop.name", read_only=True)
    price = serializers.DecimalField(source="selling_price", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "shop", "store_id", "store_name", "name", "category", "brand", "size", "description", "mrp", "selling_price", "price", "stock_quantity", "unit", "image_url"]


class ProductOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "shop", "name", "category", "description", "mrp", "selling_price", "cost_price", "stock_quantity", "unit", "image_url", "status", "brand", "size"]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["shop", "name", "category", "brand", "size", "description", "mrp", "selling_price", "cost_price", "stock_quantity", "unit", "image_url", "status"]

    def validate(self, attrs):
        if attrs.get("mrp", 0) < attrs.get("selling_price", 0):
            raise serializers.ValidationError("selling_price cannot exceed mrp")
        if attrs.get("cost_price", 0) > attrs.get("selling_price", 0):
            raise serializers.ValidationError("cost_price cannot exceed selling_price")
        return attrs
