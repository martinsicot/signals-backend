from django.contrib.auth import get_user_model
from rest_framework import serializers
from ..models import Customer, Address

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "first_name", "last_name", "company",
            "line1", "line2", "city", "postal_code", "country", "is_default",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "email", "first_name", "last_name", "phone", "addresses"]


class StaffUserSerializer(serializers.ModelSerializer):
    """Returned on login/me for crm and ops users (no Customer record)."""

    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "groups", "is_staff"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
