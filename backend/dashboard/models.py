from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        WEATHER_DELAY = "weather_delay", "Weather Delay"
        DELIVERY_CONFIRMED = "delivery_confirmed", "Delivery Confirmed"
        SYSTEM_MAINTENANCE = "system_maintenance", "System Maintenance"
        GEO_FENCE_BREACH = "geo_fence_breach", "Geo-Fence Breach"
        KYC = "kyc", "KYC Update"
        DISPUTE = "dispute", "Dispute Update"
        OTHER = "other", "Other"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Alert(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        INVESTIGATING = "investigating", "Investigating"
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"

    alert_type = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=50, blank=True)
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_alerts"
    )
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.alert_type} ({self.reference_id})"
