from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from common.pagination import DefaultPagination
from common.permissions import IsCustomer, IsDriver
from deliveries.services import haversine_miles

from .models import Address, DriverProfile, User
from .serializers import (
    AddressSerializer,
    AvailableDriverSerializer,
    CustomerRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    DriverProfileSerializer,
    DriverRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class CustomerRegistrationView(generics.CreateAPIView):
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = CustomTokenObtainPairSerializer.get_token(user)
        return Response(
            {
                "access": str(tokens.access_token),
                "refresh": str(tokens),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class DriverRegistrationView(generics.CreateAPIView):
    serializer_class = DriverRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = CustomTokenObtainPairSerializer.get_token(user)
        return Response(
            {
                "access": str(tokens.access_token),
                "refresh": str(tokens),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class DriverStatusView(APIView):
    """Toggle online/offline and (optionally) push a current lat/lng — used by the driver dashboard."""

    permission_classes = [IsDriver]

    def patch(self, request):
        profile = request.user.driver_profile
        for field in ("is_online", "current_lat", "current_lng"):
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save(update_fields=["is_online", "current_lat", "current_lng"])
        return Response(DriverProfileSerializer(profile).data)


class AvailableDriversView(generics.ListAPIView):
    """Customer-facing 'Find Drivers' directory — approved drivers only, no contact info."""

    serializer_class = AvailableDriverSerializer
    permission_classes = [IsCustomer]
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = DriverProfile.objects.filter(
            verification_status=DriverProfile.VerificationStatus.APPROVED
        ).select_related("user")
        vehicle_type = self.request.query_params.get("vehicle_type")
        if vehicle_type:
            qs = qs.filter(vehicle_type=vehicle_type)
        online_only = self.request.query_params.get("online_only")
        if online_only in ("1", "true", "True"):
            qs = qs.filter(is_online=True)
        return qs.order_by("-is_online", "-rating")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        distances = {}
        if lat and lng:
            try:
                lat, lng = float(lat), float(lng)
            except ValueError:
                lat = lng = None
            if lat is not None:
                for driver in self.get_queryset():
                    if driver.current_lat is not None and driver.current_lng is not None:
                        distances[driver.id] = haversine_miles(lat, lng, driver.current_lat, driver.current_lng)
        context["distances"] = distances
        return context


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user.customer_profile)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user.customer_profile)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # In production this is emailed to the user instead of returned.
            return Response({"detail": "Reset link generated.", "uid": uid, "token": token})
        return Response({"detail": "If that account exists, a reset link has been generated."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, data["token"]):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})
