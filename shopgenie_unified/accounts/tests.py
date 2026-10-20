from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class LoginTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@test.com",
            username="owner",
            password="pass12345",
            role="SHOP_OWNER",
        )
        self.customer = User.objects.create_user(
            email="cust@test.com",
            username="cust",
            password="pass12345",
            role="CUSTOMER",
        )
        self.client = APIClient()

    def test_successful_login_by_username(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "owner", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["id"], self.owner.id)
        self.assertEqual(resp.data["user"]["role"], "SHOP_OWNER")
        self.assertNotIn("password", resp.data)

    def test_successful_login_by_email(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "owner@test.com", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertIn("access", resp.data)
        self.assertEqual(resp.data["user"]["email"], "owner@test.com")

    def test_invalid_password(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "owner", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_unknown_account(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "nonexistent", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_missing_credentials(self):
        resp = self.client.post("/api/auth/login/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)

    def test_no_password_hash_in_response(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "owner", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertNotIn("password", resp.data)
        user_data = resp.data.get("user", {})
        self.assertNotIn("password", user_data)

    def test_inactive_user_cannot_login(self):
        self.owner.is_active = False
        self.owner.save()
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "owner", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.content)
