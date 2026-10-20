from rest_framework import serializers
from accounts.models import CustomUser


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_worker_active",
            "can_view_invoices",
            "can_confirm_bills",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class WorkerCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    is_worker_active = serializers.BooleanField(required=False, default=True)
    can_view_invoices = serializers.BooleanField(required=False, default=True)
    can_confirm_bills = serializers.BooleanField(required=False, default=True)

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
