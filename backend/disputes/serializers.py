from rest_framework import serializers

from accounts.serializers import UserSerializer
from deliveries.serializers import DeliveryRequestListSerializer

from .models import Dispute, DisputeEvidence, DisputeMessage


class DisputeMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = DisputeMessage
        fields = ["id", "dispute", "sender", "is_system", "text", "created_at"]
        read_only_fields = ["id", "dispute", "sender", "is_system", "created_at"]


class DisputeEvidenceSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = DisputeEvidence
        fields = ["id", "dispute", "uploaded_by", "image", "caption", "created_at"]
        read_only_fields = ["id", "dispute", "uploaded_by", "created_at"]


class DisputeListSerializer(serializers.ModelSerializer):
    raised_by = UserSerializer(read_only=True)
    assigned_agent = UserSerializer(read_only=True)
    delivery_reference = serializers.CharField(source="delivery.reference", read_only=True)

    class Meta:
        model = Dispute
        fields = [
            "id", "case_id", "delivery", "delivery_reference", "raised_by", "title",
            "status", "priority", "assigned_agent", "created_at",
        ]


class DisputeDetailSerializer(DisputeListSerializer):
    delivery = DeliveryRequestListSerializer(read_only=True)
    messages = DisputeMessageSerializer(many=True, read_only=True)
    evidence = DisputeEvidenceSerializer(many=True, read_only=True)

    class Meta(DisputeListSerializer.Meta):
        fields = DisputeListSerializer.Meta.fields + [
            "description", "resolution_type", "resolved_amount", "admin_note",
            "resolved_by", "resolved_at", "messages", "evidence", "updated_at",
        ]


class DisputeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ["delivery", "title", "description", "priority"]

    def create(self, validated_data):
        return Dispute.objects.create(raised_by=self.context["request"].user, **validated_data)


class DisputeResolveSerializer(serializers.Serializer):
    resolution_type = serializers.ChoiceField(choices=Dispute.Resolution.choices)
    resolved_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    admin_note = serializers.CharField(required=False, allow_blank=True)
