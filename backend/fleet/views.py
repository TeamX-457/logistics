from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import DriverProfile
from common.pagination import DefaultPagination
from common.permissions import IsAdminRole

from .serializers import (
    FleetRejectSerializer,
    FleetVerificationDetailSerializer,
    FleetVerificationListSerializer,
)


class FleetVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriverProfile.objects.select_related("user").prefetch_related("documents").all()
    permission_classes = [IsAdminRole]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["verification_status", "vehicle_type", "entity_type"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "license_number"]
    ordering_fields = ["created_at", "rating"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FleetVerificationDetailSerializer
        return FleetVerificationListSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        driver = self.get_object()
        driver.verification_status = DriverProfile.VerificationStatus.APPROVED
        driver.rejection_reason = ""
        driver.verified_at = timezone.now()
        driver.verified_by = request.user
        driver.save(update_fields=["verification_status", "rejection_reason", "verified_at", "verified_by"])
        return Response(FleetVerificationDetailSerializer(driver).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = FleetRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = self.get_object()
        driver.verification_status = DriverProfile.VerificationStatus.REJECTED
        driver.rejection_reason = serializer.validated_data.get("reason", "")
        driver.verified_at = timezone.now()
        driver.verified_by = request.user
        driver.save(update_fields=["verification_status", "rejection_reason", "verified_at", "verified_by"])
        return Response(FleetVerificationDetailSerializer(driver).data, status=status.HTTP_200_OK)
