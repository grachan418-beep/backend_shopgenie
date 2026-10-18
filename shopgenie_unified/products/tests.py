from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Shop
from products.models import Product
from decimal import Decimal

User = get_user_model()


class ProductValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="o@x.com", username="owner", password="pass12345", role="SHOP_OWNER")
        self.shop = Shop.objects.create(owner=self.owner, name="S1", status="PUBLISHED")

    def test_prices_separate(self):
        p = Product.objects.create(shop=self.shop, name="P", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"))
        self.assertEqual(p.mrp, Decimal("10"))
        self.assertEqual(p.selling_price, Decimal("8"))
        self.assertEqual(p.cost_price, Decimal("5"))
