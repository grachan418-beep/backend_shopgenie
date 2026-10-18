from rest_framework import serializers
from .models import StockAdjustment


class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = ["id", "product", "delta", "reason", "note", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("delta cannot be zero")
        return value
