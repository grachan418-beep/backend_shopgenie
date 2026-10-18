from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager


class Shop(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        SUSPENDED = "SUSPENDED", "Suspended"

    owner = models.OneToOneField(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="owned_shop",
        null=True, blank=True,
    )
    name = models.CharField(max_length=200, db_index=True)
    category = models.CharField(max_length=100, default="General", db_index=True)
    description = models.TextField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    business_hours = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shopgenie_shops"

    def __str__(self):
        return self.name


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        SHOP_OWNER = "SHOP_OWNER", "Shop Owner"
        SHOP_WORKER = "SHOP_WORKER", "Shop Worker"

    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    assigned_shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name="workers")
    is_worker_active = models.BooleanField(default=True)
    can_view_invoices = models.BooleanField(default=True)
    can_confirm_bills = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "shopgenie_users"

    @property
    def is_owner(self):
        return self.role == self.Role.SHOP_OWNER

    @property
    def is_worker(self):
        return self.role == self.Role.SHOP_WORKER

    @property
    def effective_shop(self):
        if self.role == self.Role.SHOP_OWNER:
            return getattr(self, "owned_shop", None)
        if self.role == self.Role.SHOP_WORKER and self.is_worker_active:
            return self.assigned_shop
        return None

    def __str__(self):
        return f"{self.email} [{self.role}]"
