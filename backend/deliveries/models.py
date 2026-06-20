import uuid

from django.conf import settings
from django.db import models


def generate_reference():
    return f"LP-{uuid.uuid4().hex[:8].upper()}"


class DeliveryRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        NEGOTIATING = "negotiating", "Negotiating"
        ACCEPTED = "accepted", "Accepted"
        DRIVER_ARRIVED = "driver_arrived", "Driver Arrived"
        IN_TRANSIT = "in_transit", "In Transit"
        DELAYED = "delayed", "Delayed"
        DELIVERED = "delivered", "Delivered"
        DISPUTED = "disputed", "Disputed"
        CANCELLED = "cancelled", "Cancelled"

    class PackageType(models.TextChoices):
        STANDARD_FREIGHT = "standard_freight", "Standard Freight"
        OVERSIZED_EQUIPMENT = "oversized_equipment", "Oversized Equipment"
        SMALL_PARCEL = "small_parcel", "Small Parcel"
        LIQUID_BULK = "liquid_bulk", "Liquid Bulk"

    class ServiceType(models.TextChoices):
        STANDARD = "standard", "Standard"
        PRIORITY = "priority", "Priority"

    class PaymentMethodChoice(models.TextChoices):
        WALLET = "wallet", "Company Wallet"
        CARD = "card", "Card"

    reference = models.CharField(max_length=20, unique=True, default=generate_reference, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_requests"
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_deliveries",
    )

    pickup_address = models.CharField(max_length=255)
    pickup_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    dropoff_address = models.CharField(max_length=255)
    dropoff_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dropoff_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    distance_miles = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    package_type = models.CharField(max_length=30, choices=PackageType.choices)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2)
    is_fragile = models.BooleanField(default=False)
    is_perishable = models.BooleanField(default=False)
    is_hazardous = models.BooleanField(default=False)
    is_stackable = models.BooleanField(default=False)

    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    allow_counter_offers = models.BooleanField(default=True)
    market_average_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    service_type = models.CharField(max_length=20, choices=ServiceType.choices, default=ServiceType.STANDARD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethodChoice.choices, default=PaymentMethodChoice.WALLET
    )

    delivery_otp = models.CharField(max_length=6, blank=True)
    bidding_expires_at = models.DateTimeField(null=True, blank=True)
    eta = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.reference}"


class Bid(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="bids")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bid {self.amount} on {self.delivery.reference}"


class StatusEvent(models.Model):
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=20, choices=DeliveryRequest.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.delivery.reference} -> {self.status}"


class TrackingPing(models.Model):
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="tracking_pings")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    heading = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]


class Message(models.Model):
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_messages")
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to="message_attachments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class PriceProposal(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="proposals")
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proposals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    justification = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
