from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import DefaultPagination
from common.permissions import IsAdminRole

from .models import Dispute
from .serializers import (
    DisputeCreateSerializer,
    DisputeDetailSerializer,
    DisputeEvidenceSerializer,
    DisputeListSerializer,
    DisputeMessageSerializer,
    DisputeResolveSerializer,
)


class DisputeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "priority"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Dispute.objects.select_related("delivery", "raised_by", "assigned_agent")
        if user.role == "admin":
            return qs
        return qs.filter(Q(raised_by=user) | Q(delivery__customer=user) | Q(delivery__driver=user)).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return DisputeCreateSerializer
        if self.action == "list":
            return DisputeListSerializer
        return DisputeDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dispute = serializer.save()
        return Response(DisputeDetailSerializer(dispute).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        dispute = self.get_object()
        if request.method == "GET":
            return Response(DisputeMessageSerializer(dispute.messages.select_related("sender"), many=True).data)

        serializer = DisputeMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(dispute=dispute, sender=request.user)
        return Response(DisputeMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def evidence(self, request, pk=None):
        dispute = self.get_object()
        serializer = DisputeEvidenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(dispute=dispute, uploaded_by=request.user)
        return Response(DisputeEvidenceSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminRole])
    def resolve(self, request, pk=None):
        dispute = self.get_object()
        serializer = DisputeResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        dispute.status = Dispute.Status.RESOLVED
        dispute.resolution_type = data["resolution_type"]
        dispute.resolved_amount = data.get("resolved_amount")
        dispute.admin_note = data.get("admin_note", "")
        dispute.resolved_by = request.user
        dispute.resolved_at = timezone.now()
        dispute.save()
        return Response(DisputeDetailSerializer(dispute).data)
