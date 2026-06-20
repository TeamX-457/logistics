import uuid

from django.conf import settings
from django.db import models

from deliveries.models import DeliveryRequest


def generate_case_id():
    return f"DP-{uuid.uuid4().hex[:8].upper()}"


class Dispute(models.Model):
    class Status(models.TextChoices):
        UNDER_INVESTIGATION = "under_investigation", "Under Investigation"
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Resolution(models.TextChoices):
        REFUND_CUSTOMER = "refund_customer", "Refund Customer"
        RELEASE_DRIVER = "release_driver", "Release Payment to Driver"
        PARTIAL_SETTLEMENT = "partial_settlement", "Partial Settlement"

    case_id = models.CharField(max_length=20, unique=True, default=generate_case_id, editable=False)
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="disputes")
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="disputes_raised"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UNDER_INVESTIGATION)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_disputes",
    )
    resolution_type = models.CharField(max_length=30, choices=Resolution.choices, blank=True)
    resolved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="disputes_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case_id}: {self.title}"


class DisputeMessage(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="dispute_messages"
    )
    is_system = models.BooleanField(default=False)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class DisputeEvidence(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name="evidence")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dispute_evidence")
    image = models.ImageField(upload_to="dispute_evidence/")
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
