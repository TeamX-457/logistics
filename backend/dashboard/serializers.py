from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Alert, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "category", "title", "body", "is_read", "created_at"]
        read_only_fields = fields


class AlertSerializer(serializers.ModelSerializer):
    assigned_agent = UserSerializer(read_only=True)

    class Meta:
        model = Alert
        fields = ["id", "alert_type", "reference_id", "assigned_agent", "severity", "status", "created_at"]
