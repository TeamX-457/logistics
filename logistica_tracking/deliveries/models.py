from django.conf import settings
from django.db import models


class Delivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="deliveries_as_client", on_delete=models.CASCADE
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="deliveries_as_driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    pickup_location = models.TextField()
    dropoff_location = models.TextField()
    # Optional real coordinates for the pickup/dropoff addresses above (the
    # address text itself isn't geocoded). When set, the frontend plots
    # these directly instead of falling back to a placeholder position.
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    dropoff_lat = models.FloatField(null=True, blank=True)
    dropoff_lng = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery #{self.pk} ({self.status})"


class DeliveryAcceptAttempt(models.Model):
    """
    Records each driver's accept tap for a still-unresolved delivery.
    Used to detect two drivers accepting within the same conflict window
    (see deliveries/views.py AcceptDeliveryView) — cleared once the
    delivery is assigned.
    """

    delivery = models.ForeignKey(Delivery, related_name="accept_attempts", on_delete=models.CASCADE)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("delivery", "driver")
