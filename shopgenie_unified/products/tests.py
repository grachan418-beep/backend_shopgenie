from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Shop
from products.models import Product
from inventory.models import StockAdjustment

User = get_user_model()


class ProductApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@test.com", username="owner", password="pass12345", role="SHOP_OWNER")
        self.shop = Shop.objects.create(owner=self.owner, name="Shop1", status="PUBLISHED")
        self.owner.assigned_shop = None
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.other_owner = User.objects.create_user(email="o2@test.com", username="owner2", password="pass12345", role="SHOP_OWNER")
        self.other_shop = Shop.objects.create(owner=self.other_owner, name="Shop2", status="PUBLISHED")

    def test_create_product_valid(self):
        res = self.client.post("/api/products/", {
            "shop": self.shop.id, "name": "P1", "mrp": "10.00", "selling_price": "8.00",
            "cost_price": "5.00", "stock_quantity": "3", "unit": "PIECE", "status": "PUBLISHED",
        }, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)

    def test_invalid_prices_rejected(self):
        res = self.client.post("/api/products/", {
            "shop": self.shop.id, "name": "P2", "mrp": "5.00", "selling_price": "8.00",
            "cost_price": "5.00", "stock_quantity": "1", "unit": "PIECE", "status": "PUBLISHED",
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_prices_separate(self):
        p = Product.objects.create(shop=self.shop, name="P", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"), status="PUBLISHED")
        self.assertEqual(p.mrp, Decimal("10"))
        self.assertEqual(p.selling_price, Decimal("8"))
        self.assertEqual(p.cost_price, Decimal("5"))

    def test_public_no_cost_price(self):
        Product.objects.create(shop=self.shop, name="P", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"), status="PUBLISHED")
        c = APIClient()
        res = c.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        data = res.data if isinstance(res.data, list) else res.data.get("results", res.data)
        for item in data:
            self.assertNotIn("cost_price", item)

    def test_owner_update_delete(self):
        p = Product.objects.create(shop=self.shop, name="P", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"), status="PUBLISHED")
        res = self.client.patch(f"/api/products/{p.id}/", {"name": "P2"}, format="json")
        self.assertEqual(res.status_code, 200)
        res = self.client.delete(f"/api/products/{p.id}/")
        self.assertEqual(res.status_code, 204)

    def test_customer_cannot_write(self):
        cust = User.objects.create_user(email="c@test.com", username="cust", password="pass12345", role="CUSTOMER")
        c = APIClient(); c.force_authenticate(user=cust)
        res = c.post("/api/products/", {"shop": self.shop.id, "name": "X", "mrp": "1", "selling_price": "1", "cost_price": "1", "stock_quantity": "1", "unit": "PIECE"}, format="json")
        self.assertIn(res.status_code, (401, 403))

    def test_unauth_list_ok(self):
        c = APIClient()
        res = c.get("/api/products/")
        self.assertEqual(res.status_code, 200)

    def test_cross_shop_isolation(self):
        p = Product.objects.create(shop=self.other_shop, name="Other", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"), status="PUBLISHED")
        res = self.client.get(f"/api/products/{p.id}/")
        # owner of shop1 should not see shop2 product as owner serializer? get_queryset filters by shop, so 404
        self.assertIn(res.status_code, (403, 404))


class ProductVisibilityTests(TestCase):
    def setUp(self):
        self.o_pub = User.objects.create_user(email="o_pub@x.com", username="o_pub", password="pass12345", role="SHOP_OWNER")
        self.o_draft = User.objects.create_user(email="o_draft@x.com", username="o_draft", password="pass12345", role="SHOP_OWNER")
        self.o_susp = User.objects.create_user(email="o_susp@x.com", username="o_susp", password="pass12345", role="SHOP_OWNER")
        self.pub_shop = Shop.objects.create(owner=self.o_pub, name="Published Shop", status="PUBLISHED")
        self.draft_shop = Shop.objects.create(owner=self.o_draft, name="Draft Shop", status="DRAFT")
        self.susp_shop = Shop.objects.create(owner=self.o_susp, name="Suspended Shop", status="SUSPENDED")
        self.pub_product = Product.objects.create(shop=self.pub_shop, name="Pub Item", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="PUBLISHED")
        self.draft_product = Product.objects.create(shop=self.pub_shop, name="Draft Item", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="DRAFT")
        self.pub_prod_in_draft_shop = Product.objects.create(shop=self.draft_shop, name="DraftShop Item", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="PUBLISHED")
        self.pub_prod_in_susp_shop = Product.objects.create(shop=self.susp_shop, name="SuspShop Item", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="PUBLISHED")
        self.client = APIClient()

    def test_public_listing_excludes_unpublished_products(self):
        resp = self.client.get("/api/products/")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [p["name"] for p in resp.data["results"]]
        self.assertIn("Pub Item", names)
        self.assertNotIn("Draft Item", names)

    def test_public_listing_excludes_products_from_unpublished_shops(self):
        resp = self.client.get("/api/products/")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [p["name"] for p in resp.data["results"]]
        self.assertNotIn("DraftShop Item", names)
        self.assertNotIn("SuspShop Item", names)

    def test_public_detail_blocks_unpublished_shop(self):
        resp = self.client.get(f"/api/products/{self.pub_prod_in_draft_shop.id}/")
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_public_detail_blocks_suspended_shop(self):
        resp = self.client.get(f"/api/products/{self.pub_prod_in_susp_shop.id}/")
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_public_detail_visible_published(self):
        resp = self.client.get(f"/api/products/{self.pub_product.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["name"], "Pub Item")

    def test_public_store_name_present(self):
        resp = self.client.get(f"/api/products/{self.pub_product.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["store_name"], "Published Shop")

    def test_public_no_cost_price(self):
        resp = self.client.get(f"/api/products/{self.pub_product.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertNotIn("cost_price", resp.data)

    def test_public_no_owner_fields(self):
        resp = self.client.get(f"/api/products/{self.pub_product.id}/")
        self.assertEqual(resp.status_code, 200, resp.content)
        for field in ["owner", "owner_username", "email"]:
            self.assertNotIn(field, resp.data)

    def test_search_by_name(self):
        resp = self.client.get("/api/products/?search=Pub Item")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [p["name"] for p in resp.data["results"]]
        self.assertEqual(names, ["Pub Item"])

    def test_filter_by_shop(self):
        resp = self.client.get(f"/api/products/?shop={self.pub_shop.id}")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [p["name"] for p in resp.data["results"]]
        self.assertIn("Pub Item", names)

    def test_filter_by_category(self):
        Product.objects.create(shop=self.pub_shop, name="Electronic Item", category="Electronics", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("1"), status="PUBLISHED")
        resp = self.client.get("/api/products/?category=Electronics")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [p["name"] for p in resp.data["results"]]
        self.assertIn("Electronic Item", names)

    def test_pagination(self):
        resp = self.client.get("/api/products/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)



class InventoryApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@test.com", username="owner", password="pass12345", role="SHOP_OWNER")
        self.shop = Shop.objects.create(owner=self.owner, name="Shop1", status="PUBLISHED")
        self.product = Product.objects.create(shop=self.shop, name="P", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="PUBLISHED")
        self.client = APIClient(); self.client.force_authenticate(user=self.owner)

    def test_valid_adjustment(self):
        res = self.client.post("/api/inventory/", {"product": self.product.id, "delta": "2", "reason": "RESTOCK"}, format="json")
        self.assertEqual(res.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("7"))

    def test_negative_stock_rejected(self):
        res = self.client.post("/api/inventory/", {"product": self.product.id, "delta": "-10", "reason": "DAMAGE"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_adjustment_record(self):
        self.client.post("/api/inventory/", {"product": self.product.id, "delta": "1", "reason": "CORRECTION"}, format="json")
        adj = StockAdjustment.objects.first()
        self.assertEqual(adj.product_id, self.product.id)
        self.assertEqual(adj.actor_id, self.owner.id)
        self.assertEqual(adj.delta, Decimal("1"))

    def test_cross_shop_adjustment_rejected(self):
        other_owner = User.objects.create_user(email="o2@test.com", username="owner2", password="pass12345", role="SHOP_OWNER")
        other_shop = Shop.objects.create(owner=other_owner, name="S2", status="PUBLISHED")
        other_product = Product.objects.create(shop=other_shop, name="P2", mrp=Decimal("10"), selling_price=Decimal("8"), cost_price=Decimal("5"), stock_quantity=Decimal("5"), status="PUBLISHED")
        res = self.client.post("/api/inventory/", {"product": other_product.id, "delta": "1", "reason": "RESTOCK"}, format="json")
        self.assertIn(res.status_code, (403, 400))
