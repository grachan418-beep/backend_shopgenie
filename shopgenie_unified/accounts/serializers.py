from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from django.db import models
from accounts.models import CustomUser


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError(
                "Username and password are required."
            )

        user = CustomUser.objects.filter(
            models.Q(username=username) | models.Q(email=username)
        ).first()

        if user is None or not check_password(password, user.password):
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        attrs["user"] = user
        return attrs
