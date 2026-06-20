from decimal import Decimal

from django.db import transaction
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import DefaultPagination
from common.permissions import IsAdminRole

from .models import PaymentMethod, Settlement, Transaction, Wallet
from .serializers import (
    PaymentMethodSerializer,
    SettlementSerializer,
    TransactionSerializer,
    TransferSerializer,
    WalletSerializer,
    WithdrawSerializer,
)

RANGE_MONTHS = {"1M": 1, "6M": 6, "1Y": 12}


def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_or_create_wallet(self.request.user)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "status"]
    search_fields = ["transaction_id", "counterparty"]
    ordering_fields = ["created_at", "amount"]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Transaction.objects.select_related("wallet__user")
        return Transaction.objects.filter(wallet__user=self.request.user)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        method = self.get_object()
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        method.is_default = True
        method.save(update_fields=["is_default"])
        return Response(PaymentMethodSerializer(method).data)


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        wallet = get_or_create_wallet(request.user)
        serializer = WithdrawSerializer(data=request.data, context={"wallet": wallet})
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        method = serializer.validated_data["payment_method"]

        wallet.balance -= amount
        wallet.save(update_fields=["balance"])
        txn = Transaction.objects.create(
            wallet=wallet,
            category=Transaction.Category.WITHDRAWAL,
            amount=-amount,
            counterparty=method.label,
            status=Transaction.Status.PROCESSING,
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        wallet = get_or_create_wallet(request.user)
        serializer = TransferSerializer(data=request.data, context={"wallet": wallet, "request": request})
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        recipient = serializer.validated_data["recipient"]
        recipient_wallet = get_or_create_wallet(recipient)

        wallet.balance -= amount
        wallet.save(update_fields=["balance"])
        recipient_wallet.balance += amount
        recipient_wallet.save(update_fields=["balance"])

        Transaction.objects.create(
            wallet=wallet, category=Transaction.Category.WITHDRAWAL, amount=-amount,
            counterparty=recipient.email, status=Transaction.Status.COMPLETED,
        )
        txn = Transaction.objects.create(
            wallet=recipient_wallet, category=Transaction.Category.DEPOSIT, amount=amount,
            counterparty=request.user.email, status=Transaction.Status.COMPLETED,
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class SpendingSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_key = request.query_params.get("range", "1M")
        months = RANGE_MONTHS.get(range_key, 1)
        since = timezone.now() - timezone.timedelta(days=months * 31)

        wallet = get_or_create_wallet(request.user)
        qs = (
            Transaction.objects.filter(wallet=wallet, amount__lt=0, created_at__gte=since)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )
        series = [{"month": row["month"].strftime("%Y-%m"), "total": abs(row["total"])} for row in qs]
        total_spent = sum((row["total"] for row in series), Decimal("0.00"))
        return Response({"range": range_key, "total": total_spent, "series": series})


class SettlementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["entity_type", "status"]
    search_fields = ["entity_name"]
