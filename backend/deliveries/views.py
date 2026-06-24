from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import DefaultPagination

from .models import Bid, DeliveryRequest, Message, PriceProposal, StatusEvent, TrackingPing
from .serializers import (
    BidSerializer,
    DeliveryEstimateSerializer,
    DeliveryRequestCreateSerializer,
    DeliveryRequestDetailSerializer,
    DeliveryRequestListSerializer,
    MessageSerializer,
    PriceProposalSerializer,
    TrackingPingSerializer,
)
from .services import estimate_market_price, generate_otp, haversine_miles


def broadcast(group_prefix, delivery_id, event, data):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"{group_prefix}_{delivery_id}", {"type": "broadcast_event", "payload": {"event": event, "data": data}}
    )


class DeliveryRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "package_type", "service_type"]
    ordering_fields = ["created_at", "target_price", "eta"]

    def get_queryset(self):
        user = self.request.user
        qs = DeliveryRequest.objects.select_related("customer", "driver")
        if user.role == "customer":
            return qs.filter(customer=user)
        if user.role == "driver":
            from django.db.models import Q
            return qs.filter(Q(driver=user) | Q(status=DeliveryRequest.Status.PENDING, driver__isnull=True))
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return DeliveryRequestCreateSerializer
        if self.action == "list":
            return DeliveryRequestListSerializer
        return DeliveryRequestDetailSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != "customer":
            raise PermissionDenied("Only customers can create delivery requests.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery = serializer.save()
        return Response(DeliveryRequestDetailSerializer(delivery).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def marketplace(self, request):
        qs = DeliveryRequest.objects.filter(
            status=DeliveryRequest.Status.PENDING, driver__isnull=True
        ).select_related("customer")
        package_type = request.query_params.get("package_type")
        if package_type:
            qs = qs.filter(package_type=package_type)

        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        if lat and lng:
            try:
                lat, lng = float(lat), float(lng)
            except ValueError:
                lat = lng = None
        else:
            lat = lng = None

        if lat is not None:
            deliveries = list(qs)
            for delivery in deliveries:
                delivery.driver_distance_miles = (
                    haversine_miles(lat, lng, delivery.pickup_lat, delivery.pickup_lng)
                    if delivery.pickup_lat is not None and delivery.pickup_lng is not None
                    else None
                )
            deliveries.sort(key=lambda d: (d.driver_distance_miles is None, d.driver_distance_miles))
            page = self.paginate_queryset(deliveries)
            serializer = DeliveryRequestListSerializer(page or deliveries, many=True)
            data = serializer.data
            for item, delivery in zip(data, page or deliveries):
                item["distance_miles_from_driver"] = (
                    float(delivery.driver_distance_miles) if delivery.driver_distance_miles is not None else None
                )
            return self.get_paginated_response(data) if page is not None else Response(data)

        page = self.paginate_queryset(qs)
        serializer = DeliveryRequestListSerializer(page or qs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["post"])
    def estimate(self, request):
        serializer = DeliveryEstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        coords = [data.get(f) for f in ("pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng")]
        distance = haversine_miles(*coords) if all(c is not None for c in coords) else None
        market_average_price = (
            estimate_market_price(distance, data["weight_kg"], data["package_type"]) if distance is not None else None
        )
        return Response({"distance_miles": distance, "market_average_price": market_average_price})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        delivery = self.get_object()
        if delivery.status in (DeliveryRequest.Status.DELIVERED, DeliveryRequest.Status.CANCELLED):
            raise ValidationError("This delivery can no longer be cancelled.")
        delivery.status = DeliveryRequest.Status.CANCELLED
        delivery.save(update_fields=["status", "updated_at"])
        StatusEvent.objects.create(delivery=delivery, status=delivery.status)
        return Response(DeliveryRequestDetailSerializer(delivery).data)

    @action(detail=True, methods=["post"], url_path="accept-load")
    def accept_load(self, request, pk=None):
        delivery = self.get_object()
        if request.user.role != "driver":
            raise PermissionDenied("Only drivers can accept loads.")
        if delivery.driver_id is not None or delivery.status != DeliveryRequest.Status.PENDING:
            raise ValidationError("This load is no longer available.")
        delivery.driver = request.user
        delivery.final_price = delivery.target_price
        delivery.status = DeliveryRequest.Status.ACCEPTED
        delivery.delivery_otp = generate_otp()
        delivery.save(update_fields=["driver", "final_price", "status", "delivery_otp", "updated_at"])
        StatusEvent.objects.create(delivery=delivery, status=delivery.status, note="Load accepted by driver")
        return Response(DeliveryRequestDetailSerializer(delivery).data)

    @action(detail=True, methods=["post"], url_path="advance-status")
    def advance_status(self, request, pk=None):
        delivery = self.get_object()
        new_status = request.data.get("status")
        otp = request.data.get("otp")
        if new_status not in DeliveryRequest.Status.values:
            raise ValidationError({"status": "Invalid status value."})
        if new_status == DeliveryRequest.Status.DELIVERED:
            if delivery.delivery_otp and otp != delivery.delivery_otp:
                raise ValidationError({"otp": "Incorrect delivery OTP."})
        delivery.status = new_status
        delivery.save(update_fields=["status", "updated_at"])
        StatusEvent.objects.create(delivery=delivery, status=new_status, note=request.data.get("note", ""))
        return Response(DeliveryRequestDetailSerializer(delivery).data)

    @action(detail=True, methods=["get", "post"])
    def bids(self, request, pk=None):
        delivery = self.get_object()
        if request.method == "GET":
            serializer = BidSerializer(delivery.bids.select_related("driver"), many=True)
            return Response(serializer.data)

        if request.user.role != "driver":
            raise PermissionDenied("Only drivers can submit bids.")
        serializer = BidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bid = serializer.save(delivery=delivery, driver=request.user)
        delivery.status = DeliveryRequest.Status.NEGOTIATING
        delivery.save(update_fields=["status", "updated_at"])
        broadcast("marketplace", delivery.id, "new_bid", BidSerializer(bid).data)
        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path=r"bids/(?P<bid_id>\d+)/accept")
    def accept_bid(self, request, pk=None, bid_id=None):
        delivery = self.get_object()
        bid = delivery.bids.filter(id=bid_id).first()
        if bid is None:
            raise ValidationError("Bid not found.")
        bid.status = Bid.Status.ACCEPTED
        bid.save(update_fields=["status"])
        delivery.bids.exclude(id=bid.id).update(status=Bid.Status.REJECTED)
        delivery.driver = bid.driver
        delivery.final_price = bid.amount
        delivery.status = DeliveryRequest.Status.ACCEPTED
        delivery.delivery_otp = generate_otp()
        delivery.save(update_fields=["driver", "final_price", "status", "delivery_otp", "updated_at"])
        StatusEvent.objects.create(delivery=delivery, status=delivery.status, note=f"Bid #{bid.id} accepted")
        return Response(DeliveryRequestDetailSerializer(delivery).data)

    @action(detail=True, methods=["post"], url_path=r"bids/(?P<bid_id>\d+)/reject")
    def reject_bid(self, request, pk=None, bid_id=None):
        delivery = self.get_object()
        bid = delivery.bids.filter(id=bid_id).first()
        if bid is None:
            raise ValidationError("Bid not found.")
        bid.status = Bid.Status.REJECTED
        bid.save(update_fields=["status"])
        return Response(BidSerializer(bid).data)

    @action(detail=True, methods=["get", "post"])
    def tracking(self, request, pk=None):
        delivery = self.get_object()
        if request.method == "GET":
            pings = delivery.tracking_pings.all()[:50]
            return Response(
                {
                    "milestones": [
                        {"status": e.status, "note": e.note, "created_at": e.created_at}
                        for e in delivery.status_events.all()
                    ],
                    "pings": TrackingPingSerializer(pings, many=True).data,
                    "eta": delivery.eta,
                    "delivery_otp": delivery.delivery_otp if request.user == delivery.customer else None,
                }
            )

        if request.user != delivery.driver:
            raise PermissionDenied("Only the assigned driver can post location updates.")
        serializer = TrackingPingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ping = serializer.save(delivery=delivery)
        broadcast("tracking", delivery.id, "tracking_update", TrackingPingSerializer(ping).data)
        return Response(TrackingPingSerializer(ping).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        delivery = self.get_object()
        if request.method == "GET":
            return Response(MessageSerializer(delivery.messages.select_related("sender"), many=True).data)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(delivery=delivery, sender=request.user)
        broadcast("chat", delivery.id, "new_message", MessageSerializer(message).data)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def proposals(self, request, pk=None):
        delivery = self.get_object()
        if request.method == "GET":
            return Response(PriceProposalSerializer(delivery.proposals.select_related("proposed_by"), many=True).data)

        serializer = PriceProposalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save(delivery=delivery, proposed_by=request.user)
        return Response(PriceProposalSerializer(proposal).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path=r"proposals/(?P<proposal_id>\d+)/accept")
    def accept_proposal(self, request, pk=None, proposal_id=None):
        delivery = self.get_object()
        proposal = delivery.proposals.filter(id=proposal_id).first()
        if proposal is None:
            raise ValidationError("Proposal not found.")
        proposal.status = PriceProposal.Status.ACCEPTED
        proposal.save(update_fields=["status"])
        delivery.final_price = proposal.amount
        delivery.save(update_fields=["final_price", "updated_at"])
        return Response(DeliveryRequestDetailSerializer(delivery).data)

    @action(detail=True, methods=["post"], url_path=r"proposals/(?P<proposal_id>\d+)/decline")
    def decline_proposal(self, request, pk=None, proposal_id=None):
        delivery = self.get_object()
        proposal = delivery.proposals.filter(id=proposal_id).first()
        if proposal is None:
            raise ValidationError("Proposal not found.")
        proposal.status = PriceProposal.Status.DECLINED
        proposal.save(update_fields=["status"])
        return Response(PriceProposalSerializer(proposal).data)
