from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from deliveries.models import Delivery


def _auth_client(user):
    api_client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class LocationUpdateTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(username="clientA", password="pw12345678", role=User.Role.CLIENT)
        self.driver = User.objects.create_user(username="driverA", password="pw12345678", role=User.Role.DRIVER)
        self.other_driver = User.objects.create_user(username="driverB", password="pw12345678", role=User.Role.DRIVER)
        self.delivery = Delivery.objects.create(
            client=self.client_user,
            driver=self.driver,
            pickup_location="A",
            dropoff_location="B",
            status=Delivery.Status.ACCEPTED,
        )
        self.driver_client = _auth_client(self.driver)
        self.other_driver_client = _auth_client(self.other_driver)

    def test_assigned_driver_can_post_gps_update(self):
        response = self.driver_client.post(
            "/api/location/update/",
            {"delivery_id": self.delivery.id, "latitude": 4.98, "longitude": 7.4},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_first_gps_update_flips_accepted_to_in_transit(self):
        self.driver_client.post(
            "/api/location/update/",
            {"delivery_id": self.delivery.id, "latitude": 4.98, "longitude": 7.4},
            format="json",
        )
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.IN_TRANSIT)

    def test_non_assigned_driver_cannot_post_gps_update(self):
        response = self.other_driver_client.post(
            "/api/location/update/",
            {"delivery_id": self.delivery.id, "latitude": 4.98, "longitude": 7.4},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_latest_location_returns_cached_value(self):
        """
        Exercises the Redis-or-fallback cache path in tracking/redis_client.py.
        Redis isn't reachable in local/test settings, so this hits the
        in-process fallback dict — the same code path `get_latest_location`
        takes when real Redis is up, just a different backing store.
        """
        self.driver_client.post(
            "/api/location/update/",
            {"delivery_id": self.delivery.id, "latitude": 4.981, "longitude": 7.401},
            format="json",
        )

        response = self.driver_client.get(f"/api/location/{self.delivery.id}/latest/")
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.data["latitude"], 4.981)
        self.assertAlmostEqual(response.data["longitude"], 7.401)
