from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from django.db import models, transaction
from accounts.models import CustomUser, Shop
from django.core.exceptions import ValidationError


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


class RegisterCustomerSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=password,
            role=CustomUser.Role.CUSTOMER,
        )
        return user


class RegisterOwnerSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    shop_name = serializers.CharField(required=True, max_length=200)

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        shop_name = validated_data.pop("shop_name")

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=validated_data["email"],
                username=validated_data["username"],
                password=password,
                role=CustomUser.Role.SHOP_OWNER,
            )

            shop = Shop.objects.create(
                owner=user,
                name=shop_name,
                status=Shop.Status.DRAFT,
            )

        return user, shop
