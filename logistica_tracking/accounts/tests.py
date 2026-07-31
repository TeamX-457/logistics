from django.test import TestCase
from rest_framework.test import APIClient

from .models import User


class RegistrationTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()

    def test_driver_registration_creates_driver_and_returns_tokens(self):
        response = self.client_api.post(
            "/api/auth/register/driver/",
            {"username": "driver1", "email": "driver1@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["role"], User.Role.DRIVER)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(User.objects.get(username="driver1").role, User.Role.DRIVER)

    def test_client_registration_creates_client_and_returns_tokens(self):
        response = self.client_api.post(
            "/api/auth/register/client/",
            {"username": "client1", "email": "client1@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["role"], User.Role.CLIENT)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(User.objects.get(username="client1").role, User.Role.CLIENT)


class LoginTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.driver = User.objects.create_user(username="driverx", password="password123", role=User.Role.DRIVER)
        self.client_user = User.objects.create_user(username="clientx", password="password123", role=User.Role.CLIENT)
        self.admin = User.objects.create_user(username="adminx", password="password123", role=User.Role.ADMIN)

    def test_login_with_correct_role_succeeds(self):
        response = self.client_api.post(
            "/api/auth/login/",
            {"username": "driverx", "password": "password123", "role": "driver"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "driverx")

    def test_login_with_mismatched_role_fails(self):
        response = self.client_api.post(
            "/api/auth/login/",
            {"username": "driverx", "password": "password123", "role": "client"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_login_rejects_non_admin_users(self):
        response = self.client_api.post(
            "/api/auth/admin/login/",
            {"username": "driverx", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_login_accepts_admin_user(self):
        response = self.client_api.post(
            "/api/auth/admin/login/",
            {"username": "adminx", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], User.Role.ADMIN)
