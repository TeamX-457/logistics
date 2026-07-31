from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer

from .models import PriorityList


class PriorityListSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    added_by = UserSerializer(read_only=True)

    class Meta:
        model = PriorityList
        fields = ["id", "driver", "added_by", "created_at"]


class PriorityListCreateSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Role.DRIVER))

    class Meta:
        model = PriorityList
        fields = ["id", "driver"]
