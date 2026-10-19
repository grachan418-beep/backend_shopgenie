from rest_framework import serializers
from accounts.models import Shop


class ShopPublicSerializer(serializers.ModelSerializer):
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
            "rating",
            "status",
        ]
