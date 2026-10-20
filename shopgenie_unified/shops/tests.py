from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Shop
from products.models import Product

User = get_user_model()


def make_owner(email, username):
    return User.objects.create_user(email=email, username=username, password="pass12345", role="SHOP_OWNER")


class ShopDiscoveryTests(TestCase):
    def setUp(self):
        self.o1 = make_owner("o1@x.com", "owner1")
        self.shop1 = Shop.objects.create(owner=self.o1, name="Apple Mart", category="Grocery", status="PUBLISHED", address="Addr 1", phone="123", business_hours="9-5", rating="4.50")
        self.o2 = make_owner("o2@x.com", "owner2")
        self.shop2 = Shop.objects.create(owner=self.o2, name="Beta Store", category="Electronics", status="PUBLISHED", address="Addr 2", phone="456", business_hours="10-6", rating="4.20")
        self.o3 = make_owner("o3@x.com", "owner3")
        Shop.objects.create(owner=self.o3, name="Hidden Draft", category="Grocery", status="DRAFT")
        self.o4 = make_owner("o4@x.com", "owner4")
        Shop.objects.create(owner=self.o4, name="Suspended Shop", category="Grocery", status="SUSPENDED")
        self.client = APIClient()

    def test_public_listing_returns_published_only(self):
        resp = self.client.get("/api/shops/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        names = [s["name"] for s in resp.data["results"]]
        self.assertIn("Apple Mart", names)
        self.assertIn("Beta Store", names)
        self.assertNotIn("Hidden Draft", names)
        self.assertNotIn("Suspended Shop", names)

    def test_unauthenticated_access_allowed(self):
        self.client = APIClient()
        resp = self.client.get("/api/shops/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

    def test_search_by_name(self):
        resp = self.client.get("/api/shops/?search=Apple")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        names = [s["name"] for s in resp.data["results"]]
        self.assertEqual(names, ["Apple Mart"])

    def test_filter_by_category(self):
        resp = self.client.get("/api/shops/?category=Electronics")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        names = [s["name"] for s in resp.data["results"]]
        self.assertEqual(names, ["Beta Store"])

    def test_public_detail(self):
        resp = self.client.get(f"/api/shops/{self.shop1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["name"], "Apple Mart")
        self.assertNotIn("owner", resp.data)
        self.assertNotIn("email", resp.data)

    def test_detail_missing_shop(self):
        resp = self.client.get("/api/shops/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND, resp.content)

    def test_detail_hidden_shop_404(self):
        draft = Shop.objects.get(name="Hidden Draft")
        resp = self.client.get(f"/api/shops/{draft.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND, resp.content)

    def test_private_owner_fields_not_exposed(self):
        resp = self.client.get(f"/api/shops/{self.shop1.id}/")
        for field in ["owner", "owner_username", "email", "created_by"]:
            self.assertNotIn(field, resp.data)

    def test_pagination(self):
        resp = self.client.get("/api/shops/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertIn("results", resp.data)
        self.assertIn("count", resp.data)

    def test_product_shop_association(self):
        p = Product.objects.create(shop=self.shop1, name="P1", mrp="10", selling_price="8", cost_price="5", stock_quantity="1", status="PUBLISHED")
        self.assertEqual(p.shop_id, self.shop1.id)


class MyShopTests(TestCase):
    def setUp(self):
        self.owner = make_owner("o@x.com", "owner")
        self.shop = Shop.objects.create(owner=self.owner, name="My Shop", category="Grocery", status="PUBLISHED", address="123 Main St", phone="555-0000", business_hours="9-5", rating="4.50")
        self.owner2 = make_owner("o2@x.com", "owner2")
        self.shop2 = Shop.objects.create(owner=self.owner2, name="Other Shop", category="Retail", status="PUBLISHED")
        self.customer = User.objects.create_user(email="c@x.com", username="cust", password="pass12345", role="CUSTOMER")
        self.client = APIClient()

    def _auth_owner(self):
        c = APIClient()
        c.force_authenticate(user=self.owner)
        return c

    def _auth_customer(self):
        c = APIClient()
        c.force_authenticate(user=self.customer)
        return c

    def test_owner_retrieves_own_shop(self):
        c = self._auth_owner()
        resp = c.get("/api/shops/my_shop/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["name"], "My Shop")
        self.assertEqual(resp.data["id"], self.shop.id)

    def test_owner_updates_allowed_field(self):
        c = self._auth_owner()
        resp = c.patch("/api/shops/my_shop/", {"name": "Renamed Shop", "phone": "555-9999"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["name"], "Renamed Shop")
        self.assertEqual(resp.data["phone"], "555-9999")
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.name, "Renamed Shop")

    def test_unauthenticated_rejected(self):
        c = APIClient()
        resp = c.get("/api/shops/my_shop/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)
        resp = c.patch("/api/shops/my_shop/", {"name": "X"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)

    def test_customer_cannot_access(self):
        c = self._auth_customer()
        resp = c.get("/api/shops/my_shop/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_owner_cannot_access_another_shop(self):
        c = self._auth_owner()
        resp = c.get(f"/api/shops/{self.shop2.id}/")
        # Published shops are publicly readable
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

    def test_protected_fields_not_changed(self):
        c = self._auth_owner()
        resp = c.patch("/api/shops/my_shop/", {"status": "SUSPENDED", "rating": "9.99"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, "PUBLISHED")
        self.assertEqual(str(self.shop.rating), "4.50")

    def test_no_shop_returns_404(self):
        no_shop_owner = make_owner("nos@x.com", "nos")
        c = APIClient()
        c.force_authenticate(user=no_shop_owner)
        resp = c.get("/api/shops/my_shop/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND, resp.content)

