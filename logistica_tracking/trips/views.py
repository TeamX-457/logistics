from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from accounts.permissions import IsClientRole, IsDriverRole

from .models import TripSummary
from .serializers import TripSummarySerializer


class ClientTripSummaryView(generics.RetrieveAPIView):
    """Client-only. Returns the trip summary for the caller's own completed delivery."""

    permission_classes = [permissions.IsAuthenticated, IsClientRole]
    serializer_class = TripSummarySerializer

    def get_object(self):
        return get_object_or_404(
            TripSummary, delivery_id=self.kwargs["delivery_id"], delivery__client=self.request.user
        )


class DriverTripSummaryView(generics.RetrieveAPIView):
    """Driver-only. Returns the trip summary for a delivery the caller drove."""

    permission_classes = [permissions.IsAuthenticated, IsDriverRole]
    serializer_class = TripSummarySerializer

    def get_object(self):
        return get_object_or_404(
            TripSummary, delivery_id=self.kwargs["delivery_id"], delivery__driver=self.request.user
        )
