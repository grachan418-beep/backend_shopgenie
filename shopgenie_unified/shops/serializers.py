from rest_framework import serializers
from accounts.models import Shop


class ShopPublicSerializer(serializers.ModelSerializer):
    hours = serializers.CharField(source="business_hours", read_only=True)

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "category",
            "description",
            "address",
            "phone",
            "business_hours",
            "hours",
            "rating",
            "status",
        ]


class ShopOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "category",
            "description",
            "address",
            "phone",
            "business_hours",
            "status",
            "rating",
        ]
        read_only_fields = ["id", "status", "rating"]

