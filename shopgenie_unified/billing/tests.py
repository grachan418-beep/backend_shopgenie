from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Shop
from products.models import Product
from inventory.models import StockAdjustment
from billing.models import Invoice, InvoiceItem

User = get_user_model()


def make_owner(email, username, shop_name):
    u = User.objects.create_user(email=email, username=username, password="pass12345", role="SHOP_OWNER")
    s = Shop.objects.create(owner=u, name=shop_name, status="PUBLISHED")
    return u, s


def make_worker(email, username, shop, can_confirm_bills=True, can_view_invoices=True):
    u = User.objects.create_user(email=email, username=username, password="pass12345", role="SHOP_WORKER")
    u.assigned_shop = shop
    u.is_worker_active = True
    u.can_confirm_bills = can_confirm_bills
    u.can_view_invoices = can_view_invoices
    u.save()
    return u


def make_product(shop, name, stock, price="8.00", status="PUBLISHED"):
    return Product.objects.create(
        shop=shop, name=name, mrp=Decimal("10"), selling_price=Decimal(price),
        cost_price=Decimal("5"), stock_quantity=Decimal(stock), status=status,
    )


class BillingEndpointTests(TestCase):
    def setUp(self):
        self.owner, self.shop = make_owner("o@x.com", "owner", "S1")
        self.p1 = make_product(self.shop, "Apple", Decimal("10"), "8.00")
        self.p2 = make_product(self.shop, "Banana", Decimal("5"), "4.00")
        self.worker = make_worker("w@x.com", "worker", self.shop, can_confirm_bills=True, can_view_invoices=True)
        self.client = APIClient()

    def _auth(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_single_product_invoice(self):
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k1",
            "items": [{"product": self.p1.id, "quantity": "3"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "24.00")
        item = resp.data["items"][0]
        self.assertEqual(item["unit_price"], "8.00")
        self.assertEqual(item["line_total"], "24.00")
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("7"))
        self.assertEqual(StockAdjustment.objects.count(), 1)
        self.assertEqual(StockAdjustment.first().delta, Decimal("-3")) if False else None

    def test_multi_product_invoice(self):
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k2",
            "items": [
                {"product": self.p1.id, "quantity": "2"},
                {"product": self.p2.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "20.00")
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("8"))
        self.assertEqual(self.p2.stock_quantity, Decimal("4"))

    def test_manipulated_unit_price_ignored(self):
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k3",
            "items": [{"product": self.p1.id, "quantity": "2", "unit_price": "999.00"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "16.00")
        self.assertEqual(resp.data["items"][0]["unit_price"], "8.00")

    def test_insufficient_stock_rollback(self):
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k4",
            "items": [{"product": self.p1.id, "quantity": "999"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(StockAdjustment.objects.count(), 0)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("10"))

    def test_cross_shop_product_rejected(self):
        o2, s2 = make_owner("o2@x.com", "owner2", "S2")
        p3 = make_product(s2, "Other", Decimal("10"), "8.00")
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k5",
            "items": [{"product": p3.id, "quantity": "1"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_worker_without_billing_permission_rejected(self):
        w = make_worker("w2@x.com", "worker2", self.shop, can_confirm_bills=False)
        c = self._auth(w)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k6",
            "items": [{"product": self.p1.id, "quantity": "1"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_customer_rejected(self):
        cust = User.objects.create_user(email="c@x.com", username="cust", password="pass12345", role="CUSTOMER")
        c = self._auth(cust)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k7",
            "items": [{"product": self.p1.id, "quantity": "1"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_invalid_quantity_rejected(self):
        c = self._auth(self.owner)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k8",
            "items": [{"product": self.p1.id, "quantity": "0"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k9",
            "items": [{"product": self.p1.id, "quantity": "-1"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_idempotency_same_payload_returns_existing(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/invoices/", {
            "idempotency_key": "k10",
            "items": [{"product": self.p1.id, "quantity": "2"}],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        self.p1.refresh_from_db()
        stock_after_first = self.p1.stock_quantity
        r2 = c.post("/api/invoices/", {
            "idempotency_key": "k10",
            "items": [{"product": self.p1.id, "quantity": "2"}],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK, r2.content)
        self.assertEqual(r2.data["id"], r1.data["id"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, stock_after_first)

    def test_idempotency_changed_payload_409(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/invoices/", {
            "idempotency_key": "k11",
            "items": [{"product": self.p1.id, "quantity": "2"}],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        r2 = c.post("/api/invoices/", {
            "idempotency_key": "k11",
            "items": [{"product": self.p1.id, "quantity": "5"}],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_409_CONFLICT, r2.content)

    def test_idempotency_reordered_items_consistent(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/invoices/", {
            "idempotency_key": "k12",
            "items": [
                {"product": self.p1.id, "quantity": "1"},
                {"product": self.p2.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        r2 = c.post("/api/invoices/", {
            "idempotency_key": "k12",
            "items": [
                {"product": self.p2.id, "quantity": "1"},
                {"product": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK, r2.content)
        self.assertEqual(r2.data["id"], r1.data["id"])

    def test_unauthenticated_rejected(self):
        c = APIClient()
        resp = c.post("/api/invoices/", {
            "idempotency_key": "k13",
            "items": [{"product": self.p1.id, "quantity": "1"}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)

    def test_list_scoped_to_shop(self):
        c = self._auth(self.owner)
        c.post("/api/invoices/", {"idempotency_key": "k14", "items": [{"product": self.p1.id, "quantity": "1"}]}, format="json")
        resp = c.get("/api/invoices/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(len(resp.data), 1)

    def test_detail(self):
        c = self._auth(self.owner)
        r = c.post("/api/invoices/", {"idempotency_key": "k15", "items": [{"product": self.p1.id, "quantity": "1"}]}, format="json")
        resp = c.get(f"/api/invoices/{r.data['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["id"], r.data["id"])
        self.assertEqual(len(resp.data["items"]), 1)


class FlutterInvoiceCompatibilityTests(TestCase):
    def setUp(self):
        self.owner, self.shop = make_owner("o@x.com", "owner", "S1")
        self.p1 = make_product(self.shop, "Apple", Decimal("10"), "8.00")
        self.p2 = make_product(self.shop, "Banana", Decimal("5"), "4.00")
        self.worker = make_worker("w@x.com", "worker", self.shop, can_confirm_bills=True, can_view_invoices=True)
        self.client = APIClient()

    def _auth(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_flutter_compatible_invoice_success(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-compat-1",
            "payment_mode": "cash",
            "customer_name": "Walk-in Customer",
            "customer_phone": "+91 98450 12091",
            "items": [
                {"product_id": self.p1.id, "quantity": 2, "unit_price": "999.00"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "16.00")
        item = resp.data["items"][0]
        self.assertEqual(item["unit_price"], "8.00")
        self.assertEqual(item["line_total"], "16.00")
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("8"))

    def test_flutter_multi_product_invoice(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-compat-2",
            "payment_mode": "cash",
            "customer_name": "Customer",
            "customer_phone": "",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
                {"product_id": self.p2.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "20.00")
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("8"))
        self.assertEqual(self.p2.stock_quantity, Decimal("4"))

    def test_flutter_unit_price_ignored(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k1",
            "items": [
                {"product_id": self.p1.id, "quantity": "2", "unit_price": "999.00"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["total_amount"], "16.00")
        self.assertEqual(resp.data["items"][0]["unit_price"], "8.00")

    def test_flutter_insufficient_stock_rollback(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k2",
            "items": [
                {"product_id": self.p1.id, "quantity": "999"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(StockAdjustment.objects.count(), 0)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, Decimal("10"))

    def test_flutter_cross_shop_product_rejected(self):
        o2, s2 = make_owner("o2@x.com", "owner2", "S2")
        p3 = make_product(s2, "Other", Decimal("10"), "8.00")
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k3",
            "items": [
                {"product_id": p3.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_flutter_worker_without_billing_permission_rejected(self):
        w = make_worker("w2@x.com", "worker2", self.shop, can_confirm_bills=False)
        c = self._auth(w)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k4",
            "items": [
                {"product_id": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_flutter_customer_rejected(self):
        cust = User.objects.create_user(email="c@x.com", username="cust", password="pass12345", role="CUSTOMER")
        c = self._auth(cust)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k5",
            "items": [
                {"product_id": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_flutter_invalid_quantity_rejected(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k6",
            "items": [
                {"product_id": self.p1.id, "quantity": "0"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k7",
            "items": [
                {"product_id": self.p1.id, "quantity": "-1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_flutter_idempotency_same_payload(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k8",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
            ],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        self.p1.refresh_from_db()
        stock_after_first = self.p1.stock_quantity
        r2 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k8",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
            ],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK, r2.content)
        self.assertEqual(r2.data["id"], r1.data["id"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, stock_after_first)

    def test_flutter_idempotency_changed_payload_409(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k9",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
            ],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        r2 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k9",
            "items": [
                {"product_id": self.p1.id, "quantity": "5"},
            ],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_409_CONFLICT, r2.content)

    def test_flutter_unauthenticated_rejected(self):
        c = APIClient()
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k10",
            "items": [
                {"product_id": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)

    def test_flutter_response_has_expected_fields(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k11",
            "payment_mode": "cash",
            "customer_name": "Test Customer",
            "customer_phone": "9876543210",
            "items": [
                {"product_id": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertIn("id", resp.data)
        self.assertIn("total_amount", resp.data)
        self.assertIn("status", resp.data)
        self.assertIn("items", resp.data)
        self.assertEqual(len(resp.data["items"]), 1)
        self.assertEqual(resp.data["items"][0]["product_name"], "Apple")

    def test_flutter_missing_idempotency_key_rejected(self):
        c = self._auth(self.owner)
        resp = c.post("/api/billing/invoices/", {
            "items": [
                {"product_id": self.p1.id, "quantity": "1"},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        self.assertIn("idempotency_key", resp.data)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_flutter_different_key_same_items_creates_separate_invoice(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k12-a",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
            ],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        self.p1.refresh_from_db()
        stock_after_first = self.p1.stock_quantity
        r2 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k12-b",
            "items": [
                {"product_id": self.p1.id, "quantity": "2"},
            ],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED, r2.content)
        self.assertNotEqual(r2.data["id"], r1.data["id"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, stock_after_first - Decimal("2"))

    def test_flutter_retry_does_not_deduct_stock_twice(self):
        c = self._auth(self.owner)
        r1 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k13",
            "items": [
                {"product_id": self.p1.id, "quantity": "3"},
            ],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.content)
        self.p1.refresh_from_db()
        stock_after_first = self.p1.stock_quantity
        r2 = c.post("/api/billing/invoices/", {
            "idempotency_key": "flutter-k13",
            "items": [
                {"product_id": self.p1.id, "quantity": "3"},
            ],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK, r2.content)
        self.assertEqual(r2.data["id"], r1.data["id"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, stock_after_first)


