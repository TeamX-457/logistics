"""
Resource registry for the custom branded admin panel.

Each entry describes one model as a generically-CRUD-able "resource": which
fields are shown in the list table, which are editable vs read-only, and
which support text search. The generic views/serializers in this app read
this registry instead of having one hand-written ViewSet per model.

File/image fields are deliberately excluded from this registry — those
already have dedicated upload UIs (fleet-verification.html for driver
documents, dispute-detail.html for evidence images).
"""

from accounts.models import Address, CustomerProfile, DriverProfile, User
from dashboard.models import Alert, Notification
from deliveries.models import Bid, DeliveryRequest
from disputes.models import Dispute
from wallet.models import PaymentMethod, Settlement, Transaction, Wallet

RESOURCES = {
    "users": {
        "model": User,
        "label": "Users",
        "list_fields": ["id", "email", "first_name", "last_name", "role", "is_active", "date_joined"],
        "editable_fields": ["first_name", "last_name", "phone_number", "is_active"],
        "readonly_fields": ["id", "email", "role", "is_phone_verified", "date_joined"],
        "search_fields": ["email", "first_name", "last_name"],
        "ordering": "-date_joined",
        # New accounts go through /auth/register/ so passwords are hashed and role is
        # required at creation — this panel can manage existing users but not create raw ones.
        "creatable": False,
    },
    "customer-profiles": {
        "model": CustomerProfile,
        "label": "Customer Profiles",
        "list_fields": ["id", "user", "company_name", "account_type"],
        "editable_fields": ["user", "company_name", "account_type"],
        "readonly_fields": ["id", "created_at"],
        "search_fields": ["user__email", "company_name"],
        "ordering": "-created_at",
    },
    "addresses": {
        "model": Address,
        "label": "Addresses",
        "list_fields": ["id", "customer", "label", "city", "country", "is_default"],
        "editable_fields": ["customer", "label", "line1", "line2", "city", "state", "country", "postal_code", "is_default"],
        "readonly_fields": ["id", "lat", "lng", "created_at"],
        "search_fields": ["line1", "city", "label"],
        "ordering": "-created_at",
    },
    "driver-profiles": {
        "model": DriverProfile,
        "label": "Driver Profiles",
        "list_fields": ["id", "user", "vehicle_type", "verification_status", "tier", "rating", "is_online"],
        "editable_fields": ["user", "vehicle_type", "entity_type", "company_name", "verification_status", "tier", "rejection_reason"],
        "readonly_fields": [
            "id", "license_number", "nin_number", "date_of_birth", "rating",
            "total_trips", "is_online", "current_lat", "current_lng", "verified_at",
            "verified_by", "created_at",
        ],
        "search_fields": ["user__email", "license_number", "nin_number"],
        "ordering": "-created_at",
    },
    "deliveries": {
        "model": DeliveryRequest,
        "label": "Delivery Requests",
        "list_fields": ["id", "reference", "customer", "driver", "status", "target_price", "final_price", "created_at"],
        "editable_fields": ["customer", "driver", "status", "final_price", "eta", "payment_method"],
        "readonly_fields": [
            "id", "reference", "pickup_address", "dropoff_address",
            "distance_miles", "package_type", "weight_kg", "is_fragile", "is_perishable",
            "is_hazardous", "is_stackable", "target_price", "market_average_price",
            "service_fee", "allow_counter_offers", "service_type", "delivery_otp",
            "bidding_expires_at", "created_at", "updated_at",
        ],
        "search_fields": ["reference", "customer__email", "driver__email"],
        "ordering": "-created_at",
    },
    "bids": {
        "model": Bid,
        "label": "Bids",
        "list_fields": ["id", "delivery", "driver", "amount", "status", "created_at"],
        "editable_fields": ["delivery", "driver", "status", "amount"],
        "readonly_fields": ["id", "message", "created_at"],
        "search_fields": ["delivery__reference"],
        "ordering": "-created_at",
    },
    "disputes": {
        "model": Dispute,
        "label": "Disputes",
        "list_fields": ["id", "case_id", "title", "delivery", "status", "priority", "assigned_agent", "created_at"],
        "editable_fields": ["delivery", "raised_by", "title", "description", "status", "priority", "assigned_agent", "resolution_type", "resolved_amount", "admin_note"],
        "readonly_fields": ["id", "case_id", "resolved_by", "resolved_at", "created_at", "updated_at"],
        "search_fields": ["case_id", "title"],
        "ordering": "-created_at",
    },
    "wallets": {
        "model": Wallet,
        "label": "Wallets",
        "list_fields": ["id", "user", "balance", "currency", "updated_at"],
        "editable_fields": ["user", "balance", "currency"],
        "readonly_fields": ["id", "updated_at"],
        "search_fields": ["user__email"],
        "ordering": "-updated_at",
    },
    "payment-methods": {
        "model": PaymentMethod,
        "label": "Payment Methods",
        "list_fields": ["id", "user", "label", "method_type", "is_default", "is_verified"],
        "editable_fields": ["user", "method_type", "label", "bank_name", "is_verified", "is_default"],
        "readonly_fields": ["id", "last4", "expiry_month", "expiry_year", "created_at"],
        "search_fields": ["user__email", "label"],
        "ordering": "-created_at",
    },
    "transactions": {
        "model": Transaction,
        "label": "Transactions",
        "list_fields": ["id", "transaction_id", "wallet", "category", "amount", "status", "created_at"],
        "editable_fields": ["wallet", "category", "amount", "status", "counterparty"],
        "readonly_fields": ["id", "transaction_id", "delivery", "created_at"],
        "search_fields": ["transaction_id", "counterparty"],
        "ordering": "-created_at",
    },
    "settlements": {
        "model": Settlement,
        "label": "Settlements",
        "list_fields": ["id", "entity_name", "entity_type", "amount", "due_date", "status"],
        "editable_fields": ["entity_name", "entity_type", "amount", "due_date", "status"],
        "readonly_fields": ["id", "created_at"],
        "search_fields": ["entity_name"],
        "ordering": "due_date",
    },
    "notifications": {
        "model": Notification,
        "label": "Notifications",
        "list_fields": ["id", "recipient", "category", "title", "is_read", "created_at"],
        "editable_fields": ["recipient", "category", "title", "body", "is_read"],
        "readonly_fields": ["id", "created_at"],
        "search_fields": ["title"],
        "ordering": "-created_at",
    },
    "alerts": {
        "model": Alert,
        "label": "Alerts",
        "list_fields": ["id", "alert_type", "reference_id", "severity", "status", "assigned_agent", "created_at"],
        "editable_fields": ["alert_type", "reference_id", "assigned_agent", "severity", "status"],
        "readonly_fields": ["id", "created_at"],
        "search_fields": ["alert_type", "reference_id"],
        "ordering": "-created_at",
    },
}


def get_resource(key):
    config = RESOURCES.get(key)
    if config is None:
        from rest_framework.exceptions import NotFound
        raise NotFound(f"Unknown admin resource: {key}")
    return config
