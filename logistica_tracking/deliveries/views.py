import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from logistica_tracking.api_schema import detail_response
from accounts.models import User
from accounts.permissions import IsClientRole, IsDriverRole, IsAdminRole

from .models import Delivery, DeliveryAcceptAttempt
from .serializers import DeliveryCreateSerializer, DeliverySerializer
from .tasks import resolve_accept_conflict

logger = logging.getLogger(__name__)


class DeliveryListCreateView(generics.ListCreateAPIView):
    """
    POST: admin creates a new job request (status starts `pending`).
    GET: role-filtered, paginated delivery list — client sees their own,
    driver sees deliveries assigned to them, admin sees everything.
    Supports `?status=` filtering on GET (e.g. `?status=delivered`).
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdminRole()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        return DeliveryCreateSerializer if self.request.method == "POST" else DeliverySerializer

    def get_queryset(self):
        user = self.request.user
        qs = Delivery.objects.select_related("client", "driver").order_by("-created_at")
        if user.role == User.Role.CLIENT:
            qs = qs.filter(client=user)
        elif user.role == User.Role.DRIVER:
            qs = qs.filter(driver=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery = serializer.save()
        logger.info("Delivery %s created for client %s", delivery.id, delivery.client_id)
        return Response(DeliverySerializer(delivery).data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=None,
    responses={
        202: detail_response("AcceptDeliveryAcceptedResponse"),
        409: detail_response("AcceptDeliveryConflictResponse"),
    },
)
class AcceptDeliveryView(APIView):
    """
    Driver-only. Records this driver's accept attempt for a pending
    delivery and always returns 202 immediately — resolution happens in the
    background (see deliveries/tasks.py resolve_accept_conflict, dispatched
    via Celery) after ACCEPT_CONFLICT_WINDOW_SECONDS, to give other
    near-simultaneous taps a chance to register without blocking this
    request. Callers must not treat this response as confirmation of
    assignment: the actual outcome (job_accepted / job_taken, or nothing if
    an admin must resolve a conflict) always arrives over the driver's
    personal WebSocket channel (/ws/driver/).
    """

    permission_classes = [permissions.IsAuthenticated, IsDriverRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk)

        if delivery.status != Delivery.Status.PENDING or delivery.driver_id:
            return Response({"detail": "Job already taken."}, status=status.HTTP_409_CONFLICT)

        attempt, _ = DeliveryAcceptAttempt.objects.get_or_create(delivery=delivery, driver=request.user)
        is_first = not (
            DeliveryAcceptAttempt.objects.filter(delivery=delivery).exclude(pk=attempt.pk).exists()
        )

        if is_first:
            resolve_accept_conflict.apply_async(
                args=[delivery.id], countdown=settings.ACCEPT_CONFLICT_WINDOW_SECONDS
            )

        return Response(
            {"detail": "Your request is being processed."},
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(
    request=None,
    responses={
        200: DeliverySerializer,
        400: detail_response("ConfirmDeliveryNotInTransitResponse"),
    },
)
class ConfirmDeliveryView(APIView):
    """
    Client-only, own delivery only. Confirms a delivery that is currently
    `in_transit`, flips it to `delivered`, generates its TripSummary, and
    broadcasts `delivery_confirmed` to the delivery's tracking group and
    the assigned driver (the driver app's cue to stop posting GPS — there
    is no server-side kill switch). Returns the updated delivery.
    """

    permission_classes = [permissions.IsAuthenticated, IsClientRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk, client=request.user)

        if delivery.status != Delivery.Status.IN_TRANSIT:
            return Response(
                {"detail": "Delivery must be in transit before it can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.status = Delivery.Status.DELIVERED
        delivery.save(update_fields=["status", "updated_at"])

        from trips.services import generate_trip_summary
        from tracking.notify import notify_delivery_group, notify_driver

        generate_trip_summary(delivery)
        logger.info("Delivery %s confirmed delivered by client %s", delivery.id, request.user.id)

        payload = {"delivery_id": delivery.id}
        notify_delivery_group(delivery.id, "delivery_confirmed", payload)
        if delivery.driver_id:
            notify_driver(delivery.driver_id, "delivery_confirmed", payload)

        return Response(DeliverySerializer(delivery).data, status=status.HTTP_200_OK)
