from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentMethodViewSet,
    SettlementViewSet,
    SpendingSummaryView,
    TransactionViewSet,
    TransferView,
    WalletDetailView,
    WithdrawView,
)

router = DefaultRouter()
router.register("payment-methods", PaymentMethodViewSet, basename="payment-method")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("settlements", SettlementViewSet, basename="settlement")

urlpatterns = [
    path("wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("wallet/withdraw/", WithdrawView.as_view(), name="wallet-withdraw"),
    path("wallet/transfer/", TransferView.as_view(), name="wallet-transfer"),
    path("wallet/spending-summary/", SpendingSummaryView.as_view(), name="wallet-spending-summary"),
    path("wallet/", include(router.urls)),
]
