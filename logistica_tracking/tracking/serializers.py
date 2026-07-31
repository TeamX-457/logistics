from rest_framework import serializers

from .models import Location


class LocationUpdateSerializer(serializers.Serializer):
    delivery_id = serializers.IntegerField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "delivery", "latitude", "longitude", "timestamp"]
