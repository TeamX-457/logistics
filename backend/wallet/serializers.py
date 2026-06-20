from decimal import Decimal

from rest_framework import serializers

from accounts.models import User

from .models import PaymentMethod, Settlement, Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["balance", "currency", "updated_at"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "id", "method_type", "label", "last4", "expiry_month", "expiry_year",
            "bank_name", "is_verified", "is_default", "created_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id", "transaction_id", "delivery", "category", "amount",
            "counterparty", "status", "created_at",
        ]
        read_only_fields = fields


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())

    def validate_amount(self, value):
        wallet = self.context["wallet"]
        if value > wallet.balance:
            raise serializers.ValidationError("Insufficient wallet balance.")
        return value


class TransferSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    recipient_email = serializers.EmailField()

    def validate(self, attrs):
        wallet = self.context["wallet"]
        if attrs["amount"] > wallet.balance:
            raise serializers.ValidationError("Insufficient wallet balance.")
        try:
            attrs["recipient"] = User.objects.get(email__iexact=attrs["recipient_email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient not found.")
        if attrs["recipient"] == self.context["request"].user:
            raise serializers.ValidationError("Cannot transfer funds to yourself.")
        return attrs


class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ["id", "entity_name", "entity_type", "amount", "due_date", "status", "created_at"]
