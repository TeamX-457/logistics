from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer

from .models import Delivery


class DeliverySerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "client",
            "driver",
            "pickup_location",
            "dropoff_location",
            "pickup_lat",
            "pickup_lng",
            "dropoff_lat",
            "dropoff_lng",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DeliveryCreateSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Role.CLIENT))
    pickup_lat = serializers.FloatField(required=False, allow_null=True, min_value=-90, max_value=90)
    pickup_lng = serializers.FloatField(required=False, allow_null=True, min_value=-180, max_value=180)
    dropoff_lat = serializers.FloatField(required=False, allow_null=True, min_value=-90, max_value=90)
    dropoff_lng = serializers.FloatField(required=False, allow_null=True, min_value=-180, max_value=180)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "client",
            "pickup_location",
            "dropoff_location",
            "pickup_lat",
            "pickup_lng",
            "dropoff_lat",
            "dropoff_lng",
        ]

    def validate(self, attrs):
        for prefix in ("pickup", "dropoff"):
            lat, lng = attrs.get(f"{prefix}_lat"), attrs.get(f"{prefix}_lng")
            if (lat is None) != (lng is None):
                raise serializers.ValidationError(
                    {f"{prefix}_lat": ["Provide both latitude and longitude, or neither."]}
                )
        return attrs
