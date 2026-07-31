from django.db import models

from deliveries.models import Delivery


class Location(models.Model):
    """
    Reduced-interval GPS history for trip records (written roughly every
    LOCATION_DB_WRITE_INTERVAL_SECONDS). The high-frequency 5-10s pings
    only ever touch Redis (see redis_client.py) — they never reach here.
    """

    delivery = models.ForeignKey(Delivery, related_name="locations", on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
