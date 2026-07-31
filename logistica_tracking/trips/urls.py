from django.urls import path

from .views import ClientTripSummaryView, DriverTripSummaryView

urlpatterns = [
    path("<int:delivery_id>/summary/", ClientTripSummaryView.as_view(), name="trip-summary"),
    path("<int:delivery_id>/driver-summary/", DriverTripSummaryView.as_view(), name="trip-driver-summary"),
]
