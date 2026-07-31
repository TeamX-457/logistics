from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from deliveries.models import Delivery

from .models import TripSummary


def _auth_client(user):
    api_client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class TripSummaryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adminT", password="pw12345678", role=User.Role.ADMIN)
        self.client_user = User.objects.create_user(username="clientT", password="pw12345678", role=User.Role.CLIENT)
        self.driver = User.objects.create_user(username="driverT", password="pw12345678", role=User.Role.DRIVER)

        self.delivery = Delivery.objects.create(
            client=self.client_user,
            driver=self.driver,
            pickup_location="A",
            dropoff_location="B",
            status=Delivery.Status.IN_TRANSIT,
        )

        self.admin_client = _auth_client(self.admin)
        self.client_client = _auth_client(self.client_user)
        self.driver_client = _auth_client(self.driver)

    def test_confirming_delivery_creates_trip_summary(self):
        response = self.client_client.post(f"/api/deliveries/{self.delivery.id}/confirm/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TripSummary.objects.filter(delivery=self.delivery).exists())

    def test_client_can_read_own_trip_summary(self):
        self.client_client.post(f"/api/deliveries/{self.delivery.id}/confirm/")
        response = self.client_client.get(f"/api/trips/{self.delivery.id}/summary/")
        self.assertEqual(response.status_code, 200)

    def test_driver_can_read_own_trip_summary_via_driver_summary_endpoint(self):
        self.client_client.post(f"/api/deliveries/{self.delivery.id}/confirm/")
        response = self.driver_client.get(f"/api/trips/{self.delivery.id}/driver-summary/")
        self.assertEqual(response.status_code, 200)

    def test_admin_can_read_any_trip_summary(self):
        self.client_client.post(f"/api/deliveries/{self.delivery.id}/confirm/")
        response = self.admin_client.get(f"/api/admin/trips/{self.delivery.id}/summary/")
        self.assertEqual(response.status_code, 200)
