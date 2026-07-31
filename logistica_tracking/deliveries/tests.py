from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User

from .models import Delivery


def _auth_client(user):
    api_client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class DeliveryLifecycleTests(TestCase):
    """
    Covers the full delivery lifecycle end to end. Delivery creation is
    admin-only by design (see deliveries/views.py DeliveryListCreateView —
    "admin creates a job", not the client), so "client can create a
    delivery" is exercised here as: an admin creates it *for* a client, and
    it starts pending, which is what the model/permission design actually
    supports.
    """

    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="pw12345678", role=User.Role.ADMIN)
        self.client_user = User.objects.create_user(username="client1", password="pw12345678", role=User.Role.CLIENT)
        self.driver = User.objects.create_user(username="driver1", password="pw12345678", role=User.Role.DRIVER)
        self.driver2 = User.objects.create_user(username="driver2", password="pw12345678", role=User.Role.DRIVER)

        self.admin_client = _auth_client(self.admin)
        self.client_client = _auth_client(self.client_user)
        self.driver_client = _auth_client(self.driver)
        self.driver2_client = _auth_client(self.driver2)

    def _create_delivery(self):
        response = self.admin_client.post(
            "/api/deliveries/",
            {"client": self.client_user.id, "pickup_location": "A", "dropoff_location": "B"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return response.data["id"]

    def test_delivery_creation_starts_pending(self):
        delivery_id = self._create_delivery()
        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.status, Delivery.Status.PENDING)
        self.assertEqual(delivery.client_id, self.client_user.id)

    def test_driver_can_accept_pending_delivery(self):
        delivery_id = self._create_delivery()
        response = self.driver_client.post(f"/api/deliveries/{delivery_id}/accept/")
        self.assertEqual(response.status_code, 202)

        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.status, Delivery.Status.ACCEPTED)
        self.assertEqual(delivery.driver_id, self.driver.id)

    def test_client_can_confirm_in_transit_delivery(self):
        delivery_id = self._create_delivery()
        self.driver_client.post(f"/api/deliveries/{delivery_id}/accept/")
        self.driver_client.post(
            "/api/location/update/",
            {"delivery_id": delivery_id, "latitude": 4.98, "longitude": 7.4},
            format="json",
        )

        response = self.client_client.post(f"/api/deliveries/{delivery_id}/confirm/")
        self.assertEqual(response.status_code, 200)

        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.status, Delivery.Status.DELIVERED)

    def test_non_assigned_driver_cannot_accept_already_accepted_delivery(self):
        delivery_id = self._create_delivery()
        self.driver_client.post(f"/api/deliveries/{delivery_id}/accept/")

        response = self.driver2_client.post(f"/api/deliveries/{delivery_id}/accept/")
        self.assertEqual(response.status_code, 409)

        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.driver_id, self.driver.id)

    def test_admin_can_cancel_pending_delivery(self):
        delivery_id = self._create_delivery()
        response = self.admin_client.post(f"/api/admin/deliveries/{delivery_id}/cancel/")
        self.assertEqual(response.status_code, 200)

        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.status, Delivery.Status.CANCELLED)

    @patch("admin_panel.views.notify_driver")
    def test_admin_can_cancel_accepted_delivery_and_driver_is_notified(self, mock_notify_driver):
        delivery_id = self._create_delivery()
        self.driver_client.post(f"/api/deliveries/{delivery_id}/accept/")

        response = self.admin_client.post(f"/api/admin/deliveries/{delivery_id}/cancel/")
        self.assertEqual(response.status_code, 200)

        delivery = Delivery.objects.get(pk=delivery_id)
        self.assertEqual(delivery.status, Delivery.Status.CANCELLED)

        mock_notify_driver.assert_called_once()
        args, _ = mock_notify_driver.call_args
        self.assertEqual(args[0], self.driver.id)
        self.assertEqual(args[1], "job_cancelled")
