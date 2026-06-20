from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminOverviewView,
    AlertViewSet,
    CustomerDashboardView,
    DriverDashboardView,
    FinancialAnalyticsView,
    NotificationViewSet,
    OperationsMonitoringView,
)

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("alerts", AlertViewSet, basename="alert")

urlpatterns = [
    path("dashboard/admin-overview/", AdminOverviewView.as_view(), name="dashboard-admin-overview"),
    path("dashboard/financial-analytics/", FinancialAnalyticsView.as_view(), name="dashboard-financial-analytics"),
    path("dashboard/operations-monitoring/", OperationsMonitoringView.as_view(), name="dashboard-operations-monitoring"),
    path("dashboard/customer/", CustomerDashboardView.as_view(), name="dashboard-customer"),
    path("dashboard/driver/", DriverDashboardView.as_view(), name="dashboard-driver"),
    path("dashboard/", include(router.urls)),
]
