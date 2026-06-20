import uuid

from django.conf import settings
from django.db import models

from deliveries.models import DeliveryRequest


def generate_transaction_id():
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"


class PaymentMethod(models.Model):
    class MethodType(models.TextChoices):
        CARD = "card", "Card"
        BANK = "bank", "Bank Account"
        WALLET = "wallet", "Wallet"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    method_type = models.CharField(max_length=20, choices=MethodType.choices)
    label = models.CharField(max_length=100)
    last4 = models.CharField(max_length=4, blank=True)
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True)
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label} ({self.user.email})"


class Transaction(models.Model):
    class Category(models.TextChoices):
        DELIVERY_PAYMENT = "delivery_payment", "Delivery Payment"
        DEPOSIT = "deposit", "Deposit"
        REFUND = "refund", "Refund"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        PAYOUT = "payout", "Payout"
        COMMISSION = "commission", "Commission"

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PROCESSING = "processing", "Processing"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"

    transaction_id = models.CharField(max_length=20, unique=True, default=generate_transaction_id, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    delivery = models.ForeignKey(
        DeliveryRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    category = models.CharField(max_length=30, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    counterparty = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_id} - {self.amount}"


class Settlement(models.Model):
    class EntityType(models.TextChoices):
        ENTERPRISE = "enterprise", "Enterprise"
        GROUP = "group", "Group"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        FLAGGED = "flagged", "Flagged"

    entity_name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.entity_name} - {self.amount}"
