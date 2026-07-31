from django.urls import path

from .views import AdminLoginView, DriverAvailabilityView, LoginView, RegisterClientView, RegisterDriverView

urlpatterns = [
    path("register/driver/", RegisterDriverView.as_view(), name="register-driver"),
    path("register/client/", RegisterClientView.as_view(), name="register-client"),
    path("login/", LoginView.as_view(), name="login"),
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
    path("driver/availability/", DriverAvailabilityView.as_view(), name="driver-availability"),
]
