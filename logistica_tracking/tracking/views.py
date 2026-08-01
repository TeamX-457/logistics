import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from logistica_tracking.api_schema import detail_response
from accounts.models import User
from accounts.permissions import IsDriverRole
from deliveries.models import Delivery

from .models import Location
from .notify import notify_delivery_group
from .redis_client import get_latest_location, set_latest_location
from .serializers import LocationSerializer, LocationUpdateSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    request=LocationUpdateSerializer,
    responses={
        200: inline_serializer(
            name="LocationUpdateResponse",
            fields={
                "detail": serializers.CharField(),
                "status": serializers.CharField(),
            },
        ),
        400: detail_response("LocationUpdateInactiveResponse"),
        403: detail_response("LocationUpdateForbiddenResponse"),
    },
)
class LocationUpdateView(APIView):
    """
    Driver-only. Background GPS ping for an assigned, active delivery.
    Every ping updates Redis (or the in-process fallback) immediately for
    live tracking; only one write per LOCATION_DB_WRITE_INTERVAL_SECONDS
    lands in Postgres for trip history. The first ping after acceptance
    flips the delivery into `in_transit`. Broadcasts `location_update` to
    the delivery's tracking WebSocket group on every ping. Returns the
    delivery's current status.
    """

    permission_classes = [permissions.IsAuthenticated, IsDriverRole]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery_id = serializer.validated_data["delivery_id"]
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        delivery = get_object_or_404(Delivery, pk=delivery_id)

        if delivery.driver_id != request.user.id:
            logger.warning(
                "Rejected GPS update: driver %s is not assigned to delivery %s",
                request.user.id, delivery_id,
            )
            return Response({"detail": "You are not assigned to this delivery."}, status=status.HTTP_403_FORBIDDEN)

        if delivery.status not in (Delivery.Status.ACCEPTED, Delivery.Status.IN_TRANSIT):
            logger.warning(
                "Rejected GPS update: delivery %s is not active (status=%s)",
                delivery_id, delivery.status,
            )
            return Response({"detail": "Delivery is not active."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        if delivery.status == Delivery.Status.ACCEPTED:
            delivery.status = Delivery.Status.IN_TRANSIT
            delivery.save(update_fields=["status", "updated_at"])
            logger.info("Delivery %s: first GPS ping received, now in_transit", delivery.id)

        set_latest_location(delivery.id, latitude, longitude, now.isoformat())

        last = Location.objects.filter(delivery=delivery).order_by("-timestamp").first()
        if not last or (now - last.timestamp).total_seconds() >= settings.LOCATION_DB_WRITE_INTERVAL_SECONDS:
            Location.objects.create(delivery=delivery, latitude=latitude, longitude=longitude)

        notify_delivery_group(
            delivery.id,
            "location_update",
            {"delivery_id": delivery.id, "latitude": latitude, "longitude": longitude, "timestamp": now.isoformat()},
        )

        return Response({"detail": "ok", "status": delivery.status}, status=status.HTTP_200_OK)


@extend_schema(
    responses={
        200: inline_serializer(
            name="LatestLocationResponse",
            fields={
                "latitude": serializers.FloatField(),
                "longitude": serializers.FloatField(),
                "timestamp": serializers.DateTimeField(),
                # Present only when the answer came from the DB row rather
                # than the cache, which carries just the three fields above.
                "id": serializers.IntegerField(required=False),
                "delivery": serializers.IntegerField(required=False),
            },
        ),
        403: detail_response("LatestLocationForbiddenResponse"),
        404: detail_response("LatestLocationMissingResponse"),
    },
)
class LatestLocationView(APIView):
    """
    Any authenticated role (ownership-checked for client/driver, admin
    always allowed). Returns the most recent known location for a
    delivery: Redis (or the in-process fallback) first, falling back to
    the most recent `Location` DB row if nothing is cached yet.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, delivery_id):
        delivery = get_object_or_404(Delivery, pk=delivery_id)
        user = request.user

        if user.role == User.Role.CLIENT and delivery.client_id != user.id:
            return Response({"detail": "Not your delivery."}, status=status.HTTP_403_FORBIDDEN)
        if user.role == User.Role.DRIVER and delivery.driver_id != user.id:
            return Response({"detail": "Not your delivery."}, status=status.HTTP_403_FORBIDDEN)

        cached = get_latest_location(delivery.id)
        if cached:
            return Response(cached)

        last = Location.objects.filter(delivery=delivery).order_by("-timestamp").first()
        if not last:
            return Response({"detail": "No location data yet."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LocationSerializer(last).data)
