from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "phone_number", "is_active", "is_available"]
        read_only_fields = fields


class DriverRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "phone_number"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.DRIVER, **validated_data)
        user.set_password(password)
        user.save()
        return user


class ClientRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "phone_number"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.CLIENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[User.Role.CLIENT, User.Role.DRIVER])

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if user.role != attrs["role"]:
            # Credentials were valid but the account doesn't hold the
            # selected role — an authorization failure (403), distinct
            # from bad credentials (400) above.
            raise PermissionDenied("This account is not registered under the selected role.")
        attrs["user"] = user
        return attrs


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if user.role != User.Role.ADMIN:
            raise PermissionDenied("This account does not have admin access.")
        attrs["user"] = user
        return attrs
