from django.db import models

from deliveries.models import Delivery


class TripSummary(models.Model):
    delivery = models.OneToOneField(Delivery, related_name="trip_summary", on_delete=models.CASCADE)
    total_duration = models.DurationField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    route_snapshot = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip summary for delivery #{self.delivery_id}"
