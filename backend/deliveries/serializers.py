from decimal import Decimal

from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Bid, DeliveryRequest, Message, PriceProposal, StatusEvent, TrackingPing
from .services import estimate_market_price, haversine_miles

SERVICE_FEE_RATE = Decimal("0.025")


class StatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusEvent
        fields = ["status", "note", "created_at"]


class TrackingPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingPing
        fields = ["id", "lat", "lng", "heading", "recorded_at"]
        read_only_fields = ["id", "recorded_at"]


class BidSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "delivery", "driver", "amount", "message", "status", "created_at"]
        read_only_fields = ["id", "delivery", "driver", "status", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "delivery", "sender", "text", "attachment", "created_at"]
        read_only_fields = ["id", "delivery", "sender", "created_at"]


class PriceProposalSerializer(serializers.ModelSerializer):
    proposed_by = UserSerializer(read_only=True)

    class Meta:
        model = PriceProposal
        fields = ["id", "delivery", "proposed_by", "amount", "justification", "status", "created_at"]
        read_only_fields = ["id", "delivery", "proposed_by", "status", "created_at"]


class DeliveryRequestListSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)

    class Meta:
        model = DeliveryRequest
        fields = [
            "id", "reference", "customer", "driver", "pickup_address", "dropoff_address",
            "distance_miles", "package_type", "weight_kg", "target_price", "final_price",
            "service_type", "status", "eta", "created_at",
        ]


class DeliveryRequestDetailSerializer(DeliveryRequestListSerializer):
    status_events = StatusEventSerializer(many=True, read_only=True)
    bids = BidSerializer(many=True, read_only=True)
    proposals = PriceProposalSerializer(many=True, read_only=True)
    latest_ping = serializers.SerializerMethodField()

    class Meta(DeliveryRequestListSerializer.Meta):
        fields = DeliveryRequestListSerializer.Meta.fields + [
            "pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng",
            "is_fragile", "is_perishable", "is_hazardous", "is_stackable",
            "allow_counter_offers", "market_average_price", "service_fee",
            "payment_method", "delivery_otp", "bidding_expires_at",
            "status_events", "bids", "proposals", "latest_ping", "updated_at",
        ]

    def get_latest_ping(self, obj):
        ping = obj.tracking_pings.first()
        return TrackingPingSerializer(ping).data if ping else None


class DeliveryRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRequest
        fields = [
            "pickup_address", "pickup_lat", "pickup_lng",
            "dropoff_address", "dropoff_lat", "dropoff_lng",
            "package_type", "weight_kg", "is_fragile", "is_perishable",
            "is_hazardous", "is_stackable", "target_price", "allow_counter_offers",
            "service_type", "payment_method",
        ]

    def create(self, validated_data):
        validated_data["service_fee"] = (validated_data["target_price"] * SERVICE_FEE_RATE).quantize(Decimal("0.01"))

        coords = [validated_data.get(f) for f in ("pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng")]
        if all(c is not None for c in coords):
            distance = haversine_miles(*coords)
            validated_data["distance_miles"] = distance
            validated_data["market_average_price"] = estimate_market_price(
                distance, validated_data["weight_kg"], validated_data["package_type"]
            )

        delivery = DeliveryRequest.objects.create(customer=self.context["request"].user, **validated_data)
        StatusEvent.objects.create(delivery=delivery, status=DeliveryRequest.Status.PENDING)
        return delivery


class DeliveryEstimateSerializer(serializers.Serializer):
    pickup_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    pickup_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    dropoff_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    dropoff_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    weight_kg = serializers.DecimalField(max_digits=10, decimal_places=2)
    package_type = serializers.ChoiceField(choices=DeliveryRequest.PackageType.choices)
