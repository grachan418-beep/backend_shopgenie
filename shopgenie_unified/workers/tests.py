from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Shop

User = get_user_model()


def make_owner(email, username, shop_name):
    u = User.objects.create_user(email=email, username=username, password="pass12345", role="SHOP_OWNER")
    s = Shop.objects.create(owner=u, name=shop_name, status="PUBLISHED")
    return u, s


class WorkerManagementTests(TestCase):
    def setUp(self):
        self.owner, self.shop = make_owner("o@x.com", "owner", "S1")
        self.owner2, self.shop2 = make_owner("o2@x.com", "owner2", "S2")
        self.customer = User.objects.create_user(email="c@x.com", username="cust", password="pass12345", role="CUSTOMER")
        self.client = APIClient()

    def _auth_owner(self, user=None):
        c = APIClient()
        c.force_authenticate(user=user or self.owner)
        return c

    def _auth_customer(self):
        c = APIClient()
        c.force_authenticate(user=self.customer)
        return c

    def test_list_workers_owner(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
            is_worker_active=True, can_view_invoices=True, can_confirm_bills=True,
        )
        c = self._auth_owner()
        resp = c.get("/api/workers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["username"], "worker1")
        # No password hash exposed
        self.assertNotIn("password", resp.data[0])

    def test_list_workers_other_owner_empty(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
        )
        c = self._auth_owner(self.owner2)
        resp = c.get("/api/workers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(len(resp.data), 0)

    def test_create_worker_owner(self):
        c = self._auth_owner()
        resp = c.post("/api/workers/", {
            "username": "newworker",
            "email": "nw@x.com",
            "password": "pass12345",
            "first_name": "New",
            "last_name": "Worker",
            "can_view_invoices": True,
            "can_confirm_bills": False,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        self.assertEqual(resp.data["username"], "newworker")
        self.assertEqual(resp.data["is_worker_active"], True)
        self.assertEqual(resp.data["can_confirm_bills"], False)
        self.assertNotIn("password", resp.data)
        # Verify assigned to owner's shop
        u = User.objects.get(username="newworker")
        self.assertEqual(u.assigned_shop_id, self.shop.id)
        self.assertEqual(u.role, "SHOP_WORKER")

    def test_create_worker_duplicate_username(self):
        User.objects.create_user(email="w@x.com", username="dup", password="pass12345", role="SHOP_WORKER", assigned_shop=self.shop)
        c = self._auth_owner()
        resp = c.post("/api/workers/", {
            "username": "dup",
            "email": "dup2@x.com",
            "password": "pass12345",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_create_worker_duplicate_email(self):
        User.objects.create_user(email="dup@x.com", username="dup1", password="pass12345", role="SHOP_WORKER", assigned_shop=self.shop)
        c = self._auth_owner()
        resp = c.post("/api/workers/", {
            "username": "dup2",
            "email": "dup@x.com",
            "password": "pass12345",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_create_worker_missing_fields(self):
        c = self._auth_owner()
        resp = c.post("/api/workers/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_get_worker_detail(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
        )
        c = self._auth_owner()
        resp = c.get(f"/api/workers/{worker.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["username"], "worker1")

    def test_update_worker(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
            can_confirm_bills=True,
        )
        c = self._auth_owner()
        resp = c.patch(f"/api/workers/{worker.id}/", {
            "can_confirm_bills": False,
            "first_name": "Updated",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertEqual(resp.data["can_confirm_bills"], False)
        self.assertEqual(resp.data["first_name"], "Updated")
        worker.refresh_from_db()
        self.assertEqual(worker.can_confirm_bills, False)

    def test_cross_shop_worker_access_blocked(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop2,
        )
        c = self._auth_owner(self.owner)  # owner1 trying to access owner2's worker
        resp = c.get(f"/api/workers/{worker.id}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        resp = c.patch(f"/api/workers/{worker.id}/", {"first_name": "X"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
        resp = c.delete(f"/api/workers/{worker.id}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_delete_worker(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
        )
        c = self._auth_owner()
        resp = c.delete(f"/api/workers/{worker.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT, resp.content)
        self.assertFalse(User.objects.filter(pk=worker.id).exists())

    def test_unauthenticated_rejected(self):
        c = APIClient()
        resp = c.get("/api/workers/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)
        resp = c.post("/api/workers/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, resp.content)

    def test_customer_cannot_manage_workers(self):
        c = self._auth_customer()
        resp = c.get("/api/workers/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)
        resp = c.post("/api/workers/", {
            "username": "x", "email": "x@x.com", "password": "pass12345",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)

    def test_worker_cannot_manage_workers(self):
        worker = User.objects.create_user(
            email="w@x.com", username="worker1", password="pass12345",
            role="SHOP_WORKER", assigned_shop=self.shop,
            is_worker_active=True,
        )
        c = APIClient()
        c.force_authenticate(user=worker)
        resp = c.get("/api/workers/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.content)
