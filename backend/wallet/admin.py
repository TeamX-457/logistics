from django.contrib import admin

from .models import PaymentMethod, Settlement, Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "currency", "updated_at"]
    search_fields = ["user__email"]


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["user", "label", "method_type", "is_default", "is_verified"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_id", "wallet", "category", "amount", "status", "created_at"]
    list_filter = ["category", "status"]
    search_fields = ["transaction_id", "counterparty"]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["entity_name", "entity_type", "amount", "due_date", "status"]
    list_filter = ["entity_type", "status"]
