from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Address, CustomerProfile, DriverDocument, DriverProfile, User


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "label", "line1", "line2", "city", "state", "country",
            "postal_code", "lat", "lng", "is_default", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ["company_name", "account_type"]


class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ["id", "doc_type", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class DriverProfileSerializer(serializers.ModelSerializer):
    documents = DriverDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "vehicle_type", "license_number", "nin_number", "date_of_birth",
            "entity_type", "company_name", "verification_status", "tier",
            "rating", "total_trips", "is_online", "current_lat", "current_lng",
            "rejection_reason", "verified_at", "documents",
        ]
        read_only_fields = [
            "verification_status", "tier", "rating", "total_trips",
            "rejection_reason", "verified_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    customer_profile = CustomerProfileSerializer(read_only=True)
    driver_profile = DriverProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role", "phone_number",
            "is_phone_verified", "avatar", "customer_profile", "driver_profile",
            "created_at",
        ]
        read_only_fields = ["id", "role", "is_phone_verified", "created_at"]


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "phone_number", "password", "full_name", "company_name"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        company_name = validated_data.pop("company_name", "")
        password = validated_data.pop("password")
        first_name, _, last_name = full_name.partition(" ")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            phone_number=validated_data.get("phone_number", ""),
            first_name=first_name,
            last_name=last_name,
            role=User.Role.CUSTOMER,
        )
        CustomerProfile.objects.create(user=user, company_name=company_name)
        return user


class DriverRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(write_only=True)
    vehicle_type = serializers.ChoiceField(choices=DriverProfile.VehicleType.choices)
    license_number = serializers.CharField()
    nin_number = serializers.CharField(max_length=11)

    class Meta:
        model = User
        fields = [
            "email", "phone_number", "password", "full_name",
            "vehicle_type", "license_number", "nin_number",
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        vehicle_type = validated_data.pop("vehicle_type")
        license_number = validated_data.pop("license_number")
        nin_number = validated_data.pop("nin_number")
        password = validated_data.pop("password")
        first_name, _, last_name = full_name.partition(" ")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            phone_number=validated_data.get("phone_number", ""),
            first_name=first_name,
            last_name=last_name,
            role=User.Role.DRIVER,
        )
        DriverProfile.objects.create(
            user=user,
            vehicle_type=vehicle_type,
            license_number=license_number,
            nin_number=nin_number,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
