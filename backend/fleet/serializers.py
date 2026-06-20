from rest_framework import serializers

from accounts.models import DriverDocument, DriverProfile


class FleetDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ["id", "doc_type", "file", "uploaded_at"]


class FleetVerificationListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email")
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    registration_date = serializers.DateTimeField(source="created_at")

    class Meta:
        model = DriverProfile
        fields = [
            "id", "full_name", "email", "avatar", "entity_type", "vehicle_type",
            "registration_date", "verification_status",
        ]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class FleetVerificationDetailSerializer(FleetVerificationListSerializer):
    documents = FleetDocumentSerializer(many=True, read_only=True)
    phone_number = serializers.CharField(source="user.phone_number")

    class Meta(FleetVerificationListSerializer.Meta):
        fields = FleetVerificationListSerializer.Meta.fields + [
            "phone_number", "license_number", "nin_number", "date_of_birth",
            "company_name", "rejection_reason", "verified_at", "documents",
        ]


class FleetRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=True, required=False)
