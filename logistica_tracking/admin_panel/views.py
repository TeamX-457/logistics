import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdminRole
from accounts.serializers import UserSerializer
from deliveries.models import Delivery
from deliveries.serializers import DeliverySerializer
from deliveries.services import assign_driver
from tracking.notify import notify_delivery_group, notify_driver
from trips.models import TripSummary
from trips.serializers import TripSummarySerializer

from .models import PriorityList
from .serializers import PriorityListCreateSerializer, PriorityListSerializer

logger = logging.getLogger(__name__)


class AdminDeliveryListView(generics.ListAPIView):
    """
    Admin-only, paginated. All deliveries in the system, newest first.
    Supports `?status=`, `?client=` (client id), and `?driver=` (driver id)
    filtering, any combination of which may be supplied together.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    serializer_class = DeliverySerializer

    def get_queryset(self):
        qs = Delivery.objects.select_related("client", "driver").order_by("-created_at")
        params = self.request.query_params
        status_param = params.get("status")
        client_param = params.get("client")
        driver_param = params.get("driver")
        if status_param:
            qs = qs.filter(status=status_param)
        if client_param:
            qs = qs.filter(client_id=client_param)
        if driver_param:
            qs = qs.filter(driver_id=driver_param)
        return qs


class PriorityListView(generics.ListCreateAPIView):
    """
    Admin-only, paginated.
    GET: full priority driver list.
    POST: add (or re-affirm) a driver as priority; body: `{"driver": <id>}`.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = PriorityList.objects.select_related("driver", "added_by").order_by("-created_at")

    def get_serializer_class(self):
        return PriorityListCreateSerializer if self.request.method == "POST" else PriorityListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = serializer.validated_data["driver"]
        entry, _ = PriorityList.objects.update_or_create(driver=driver, defaults={"added_by": request.user})
        return Response(PriorityListSerializer(entry).data, status=status.HTTP_201_CREATED)


class PriorityListDeleteView(APIView):
    """Admin-only. Removes a driver from the priority list by driver id."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def delete(self, request, driver_id):
        deleted, _ = PriorityList.objects.filter(driver_id=driver_id).delete()
        if not deleted:
            return Response({"detail": "Driver is not on the priority list."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotifyAllPriorityDriversView(APIView):
    """Admin-only. Broadcasts a `job_request` WebSocket event for a pending delivery to every priority driver."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk, status=Delivery.Status.PENDING)
        driver_ids = list(PriorityList.objects.values_list("driver_id", flat=True))
        payload = {"delivery": DeliverySerializer(delivery).data}
        for driver_id in driver_ids:
            notify_driver(driver_id, "job_request", payload)
        return Response({"detail": f"Broadcast sent to {len(driver_ids)} priority drivers."})


class NotifySpecificDriverView(APIView):
    """
    Admin-only. Pushes a `job_request` WebSocket event for a pending
    delivery to one named driver — any registered driver, priority-listed
    or not.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk, driver_id):
        delivery = get_object_or_404(Delivery, pk=pk, status=Delivery.Status.PENDING)
        driver = get_object_or_404(User, pk=driver_id, role=User.Role.DRIVER)
        payload = {"delivery": DeliverySerializer(delivery).data}
        notify_driver(driver.id, "job_request", payload)
        return Response({"detail": "Notification sent."})


class NotifyEveryoneDriversView(APIView):
    """Admin-only. Broadcasts a `job_request` WebSocket event for a pending delivery to every registered driver."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk, status=Delivery.Status.PENDING)
        driver_ids = list(User.objects.filter(role=User.Role.DRIVER).values_list("id", flat=True))
        payload = {"delivery": DeliverySerializer(delivery).data}
        for driver_id in driver_ids:
            notify_driver(driver_id, "job_request", payload)
        return Response({"detail": f"Broadcast sent to {len(driver_ids)} drivers."})


class ResolveConflictView(APIView):
    """Admin-only. Manually assigns a driver to a delivery after a simultaneous-accept conflict was flagged."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk)
        driver_id = request.data.get("driver_id")
        if not driver_id:
            return Response({"detail": "driver_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        driver = get_object_or_404(User, pk=driver_id, role=User.Role.DRIVER)

        if delivery.status != Delivery.Status.PENDING or delivery.driver_id:
            return Response({"detail": "Delivery already resolved."}, status=status.HTTP_409_CONFLICT)

        assign_driver(delivery, driver, resolved_by_admin=True)
        return Response(DeliverySerializer(delivery).data)


class CancelDeliveryView(APIView):
    """
    Admin-only. Cancels a delivery that is still `pending` or `accepted`
    (a delivery already `in_transit`/`delivered` cannot be cancelled).
    Sets status to `cancelled`, notifies the assigned driver (if any) with
    a `job_cancelled` WebSocket event on their personal channel, and always
    broadcasts `job_cancelled` to the delivery's tracking group so a
    watching client is notified live too.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk)

        if delivery.status not in (Delivery.Status.PENDING, Delivery.Status.ACCEPTED):
            return Response(
                {"detail": "Only a pending or accepted delivery can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.status = Delivery.Status.CANCELLED
        delivery.save(update_fields=["status", "updated_at"])
        logger.info("Delivery %s cancelled by admin %s", delivery.id, request.user.id)

        payload = {"delivery_id": delivery.id}
        if delivery.driver_id:
            notify_driver(delivery.driver_id, "job_cancelled", payload)
        notify_delivery_group(delivery.id, "job_cancelled", payload)

        return Response(DeliverySerializer(delivery).data)


class AdminUserListView(generics.ListAPIView):
    """
    Admin-only, paginated. All users in the system.
    Supports `?role=` filtering (`client`, `driver`, or `admin`).
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    serializer_class = UserSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("id")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class DeactivateUserView(APIView):
    """
    Admin-only. Sets `is_active=False` on the user, which blocks future
    logins (Django's auth backend refuses inactive users). Any JWT access
    token already issued to the user remains valid until it expires.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info("User %s deactivated by admin %s", user.id, request.user.id)
        return Response({"detail": "User deactivated.", "user": UserSerializer(user).data})


class ActivateUserView(APIView):
    """Admin-only. Reverses deactivation by setting `is_active=True` on the user."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save(update_fields=["is_active"])
        logger.info("User %s activated by admin %s", user.id, request.user.id)
        return Response({"detail": "User activated.", "user": UserSerializer(user).data})


class AdminTripSummaryView(generics.RetrieveAPIView):
    """Admin-only. Returns the TripSummary for any delivery by delivery id."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    serializer_class = TripSummarySerializer
    lookup_field = "delivery_id"
    lookup_url_kwarg = "delivery_id"
    queryset = TripSummary.objects.select_related("delivery")
