from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    CustomerRegistrationView,
    DriverRegistrationView,
    DriverStatusView,
    LoginView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("auth/register/customer/", CustomerRegistrationView.as_view(), name="register-customer"),
    path("auth/register/driver/", DriverRegistrationView.as_view(), name="register-driver"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("drivers/me/status/", DriverStatusView.as_view(), name="driver-status"),
    path("", include(router.urls)),
]
