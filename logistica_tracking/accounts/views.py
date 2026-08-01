from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from logistica_tracking.api_schema import auth_response
from .permissions import IsDriverRole
from .serializers import (
    AdminLoginSerializer,
    ClientRegisterSerializer,
    DriverRegisterSerializer,
    LoginSerializer,
    UserSerializer,
)
from .throttling import LoginThrottle, RegisterThrottle
from .tokens import tokens_for_user


@extend_schema(
    request=DriverRegisterSerializer,
    responses={201: auth_response("DriverRegisterResponse")},
)
class RegisterDriverView(generics.CreateAPIView):
    """Public. Creates a `role=driver` user and returns a JWT token pair immediately (register = auto-login)."""

    serializer_class = DriverRegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            raise ValidationError({"username": ["A user with that username already exists."]})
        data = {"user": UserSerializer(user).data, **tokens_for_user(user)}
        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=ClientRegisterSerializer,
    responses={201: auth_response("ClientRegisterResponse")},
)
class RegisterClientView(generics.CreateAPIView):
    """Public. Creates a `role=client` user and returns a JWT token pair immediately (register = auto-login)."""

    serializer_class = ClientRegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            raise ValidationError({"username": ["A user with that username already exists."]})
        data = {"user": UserSerializer(user).data, **tokens_for_user(user)}
        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=LoginSerializer,
    responses={200: auth_response("LoginResponse")},
)
class LoginView(APIView):
    """
    Public. Logs in a client or driver; the request body must include
    `role` (`client` or `driver`) and it must match the account's actual
    role, or the login is rejected. Returns the user and a JWT token pair.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        data = {"user": UserSerializer(user).data, **tokens_for_user(user)}
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    request=AdminLoginSerializer,
    responses={200: auth_response("AdminLoginResponse")},
)
class AdminLoginView(APIView):
    """Public. Logs in an admin account only (rejects any non-admin user). Returns the user and a JWT token pair."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        data = {"user": UserSerializer(user).data, **tokens_for_user(user)}
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        name="DriverAvailabilityRequest",
        fields={"is_available": serializers.BooleanField()},
    ),
    responses={200: UserSerializer},
)
class DriverAvailabilityView(APIView):
    """
    Driver-only. Sets whether the caller is on duty. Body: `{"is_available": true|false}`.
    Purely a status flag for now — it doesn't gate which drivers receive
    `job_request` broadcasts (admin's notify actions are unaffected), but
    is visible to admin in the Drivers table.
    """

    permission_classes = [permissions.IsAuthenticated, IsDriverRole]

    def post(self, request):
        is_available = request.data.get("is_available")
        if not isinstance(is_available, bool):
            raise ValidationError({"is_available": ["This field is required and must be true or false."]})
        request.user.is_available = is_available
        request.user.save(update_fields=["is_available"])
        return Response(UserSerializer(request.user).data)
