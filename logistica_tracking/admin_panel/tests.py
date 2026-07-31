from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from deliveries.models import Delivery

from .models import PriorityList


def _auth_client(user):
    api_client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class NotifyDriverTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adminN", password="pw12345678", role=User.Role.ADMIN)
        self.client_user = User.objects.create_user(username="clientN", password="pw12345678", role=User.Role.CLIENT)
        self.priority_driver = User.objects.create_user(username="priorityN", password="pw12345678", role=User.Role.DRIVER)
        self.normal_driver = User.objects.create_user(username="normalN", password="pw12345678", role=User.Role.DRIVER)
        PriorityList.objects.create(driver=self.priority_driver, added_by=self.admin)

        self.delivery = Delivery.objects.create(
            client=self.client_user,
            pickup_location="A",
            dropoff_location="B",
            status=Delivery.Status.PENDING,
        )
        self.admin_client = _auth_client(self.admin)

    @patch("admin_panel.views.notify_driver")
    def test_notify_specific_driver_reaches_non_priority_driver(self, mock_notify_driver):
        response = self.admin_client.post(
            f"/api/admin/deliveries/{self.delivery.id}/notify/{self.normal_driver.id}/"
        )
        self.assertEqual(response.status_code, 200)
        mock_notify_driver.assert_called_once()
        args, _ = mock_notify_driver.call_args
        self.assertEqual(args[0], self.normal_driver.id)
        self.assertEqual(args[1], "job_request")

    @patch("admin_panel.views.notify_driver")
    def test_notify_everyone_reaches_all_drivers(self, mock_notify_driver):
        response = self.admin_client.post(f"/api/admin/deliveries/{self.delivery.id}/notify/everyone/")
        self.assertEqual(response.status_code, 200)
        notified_ids = {call.args[0] for call in mock_notify_driver.call_args_list}
        self.assertEqual(notified_ids, {self.priority_driver.id, self.normal_driver.id})

    @patch("admin_panel.views.notify_driver")
    def test_notify_all_priority_only_reaches_priority_drivers(self, mock_notify_driver):
        response = self.admin_client.post(f"/api/admin/deliveries/{self.delivery.id}/notify/all/")
        self.assertEqual(response.status_code, 200)
        notified_ids = {call.args[0] for call in mock_notify_driver.call_args_list}
        self.assertEqual(notified_ids, {self.priority_driver.id})
