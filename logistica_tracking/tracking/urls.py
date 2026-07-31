from django.urls import path

from .views import LatestLocationView, LocationUpdateView

urlpatterns = [
    path("location/update/", LocationUpdateView.as_view(), name="location-update"),
    path("location/<int:delivery_id>/latest/", LatestLocationView.as_view(), name="location-latest"),
]
