from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import DriverProfile
from common.permissions import IsAdminRole, IsCustomer, IsDriver
from deliveries.models import DeliveryRequest
from deliveries.serializers import DeliveryRequestDetailSerializer, DeliveryRequestListSerializer
from disputes.models import Dispute
from wallet.models import Transaction, Wallet
from wallet.serializers import TransactionSerializer

from .models import Alert, Notification
from .serializers import AlertSerializer, NotificationSerializer

ACTIVE_DELIVERY_STATUSES = [
    DeliveryRequest.Status.PENDING,
    DeliveryRequest.Status.NEGOTIATING,
    DeliveryRequest.Status.ACCEPTED,
    DeliveryRequest.Status.DRIVER_ARRIVED,
    DeliveryRequest.Status.IN_TRANSIT,
    DeliveryRequest.Status.DELAYED,
]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related("assigned_agent").all()
    serializer_class = AlertSerializer
    permission_classes = [IsAdminRole]


class AdminOverviewView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        since = timezone.now() - timedelta(days=7)
        volume = (
            DeliveryRequest.objects.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        today = timezone.now().date()
        daily_revenue = (
            Transaction.objects.filter(category=Transaction.Category.COMMISSION, created_at__date=today)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return Response(
            {
                "active_deliveries": DeliveryRequest.objects.filter(status__in=ACTIVE_DELIVERY_STATUSES).count(),
                "pending_kyc_approvals": DriverProfile.objects.filter(
                    verification_status=DriverProfile.VerificationStatus.PENDING
                ).count(),
                "daily_revenue": daily_revenue,
                "active_disputes": Dispute.objects.exclude(status=Dispute.Status.RESOLVED).count(),
                "delivery_volume": [{"day": row["day"], "count": row["count"]} for row in volume],
                "alerts": AlertSerializer(Alert.objects.all()[:10], many=True).data,
            }
        )


class FinancialAnalyticsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        commission = Transaction.objects.filter(category=Transaction.Category.COMMISSION)
        payouts = Transaction.objects.filter(category=Transaction.Category.PAYOUT)
        deposits = Transaction.objects.filter(category__in=[Transaction.Category.DEPOSIT, Transaction.Category.DELIVERY_PAYMENT])

        total_commission = commission.aggregate(total=Sum("amount"))["total"] or 0
        total_outflow = abs(payouts.aggregate(total=Sum("amount"))["total"] or 0)
        total_inflow = deposits.aggregate(total=Sum("amount"))["total"] or 0

        since = timezone.now() - timedelta(days=365)
        trends = (
            Transaction.objects.filter(created_at__gte=since, category=Transaction.Category.COMMISSION)
            .annotate(month=TruncDate("created_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )

        return Response(
            {
                "total_platform_commission": total_commission,
                "inflow_escrow": total_inflow,
                "outflow_payouts": total_outflow,
                "net_revenue": total_commission - total_outflow,
                "revenue_trends": [{"month": row["month"], "total": row["total"]} for row in trends],
            }
        )


class OperationsMonitoringView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "active_deliveries_count": DeliveryRequest.objects.filter(status__in=ACTIVE_DELIVERY_STATUSES).count(),
                "open_disputes_count": Dispute.objects.exclude(status=Dispute.Status.RESOLVED).count(),
            }
        )


class CustomerDashboardView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        user = request.user
        deliveries = DeliveryRequest.objects.filter(customer=user)
        active = deliveries.filter(status__in=ACTIVE_DELIVERY_STATUSES)
        wallet, _ = Wallet.objects.get_or_create(user=user)
        recent = deliveries.order_by("-created_at")[:5]

        return Response(
            {
                "active_shipments_count": active.count(),
                "recent_orders_count": deliveries.count(),
                "wallet_balance": wallet.balance,
                "current_shipments": DeliveryRequestListSerializer(active[:10], many=True).data,
                "recent_orders": DeliveryRequestListSerializer(recent, many=True).data,
            }
        )


class DriverDashboardView(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        user = request.user
        profile = user.driver_profile
        today = timezone.now().date()
        wallet, _ = Wallet.objects.get_or_create(user=user)

        daily_earnings = (
            Transaction.objects.filter(wallet=wallet, amount__gt=0, created_at__date=today).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        completed_today = DeliveryRequest.objects.filter(
            driver=user, status=DeliveryRequest.Status.DELIVERED, updated_at__date=today
        ).count()

        since = today - timedelta(days=6)
        weekly = (
            Transaction.objects.filter(wallet=wallet, amount__gt=0, created_at__date__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("amount"))
            .order_by("day")
        )

        active_delivery = DeliveryRequest.objects.filter(
            driver=user,
            status__in=[DeliveryRequest.Status.ACCEPTED, DeliveryRequest.Status.DRIVER_ARRIVED, DeliveryRequest.Status.IN_TRANSIT],
        ).first()

        return Response(
            {
                "daily_earnings": daily_earnings,
                "completed_deliveries_today": completed_today,
                "rating": profile.rating,
                "total_trips": profile.total_trips,
                "is_online": profile.is_online,
                "active_delivery": DeliveryRequestDetailSerializer(active_delivery).data if active_delivery else None,
                "weekly_earnings": [{"day": row["day"], "total": row["total"]} for row in weekly],
            }
        )
