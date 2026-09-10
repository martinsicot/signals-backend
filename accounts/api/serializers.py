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


class ProfileAddressSerializer(serializers.ModelSerializer):
    """Shipping address as exposed on the account profile.

    Uses ``zip_code`` on the wire while the model stores ``postal_code``.
    """

    zip_code = serializers.CharField(source="postal_code", max_length=20)

    class Meta:
        model = Address
        fields = ["line1", "line2", "zip_code", "city", "country"]
        extra_kwargs = {
            "line2": {"required": False, "allow_blank": True},
            "country": {"required": False},
        }


class ProfileSerializer(serializers.ModelSerializer):
    """Profile of the connected customer (GET/PATCH /api/account/me/).

    ``first_name``/``last_name``/``email`` live on the ``User``; ``phone`` on the
    ``Customer``; the shipping address on the customer's default ``Address``.
    Email is read-only (changing it requires separate verification).
    """

    id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True, max_length=150
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True, max_length=150
    )
    default_shipping_address = ProfileAddressSerializer(required=False, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            "id", "email", "first_name", "last_name", "phone",
            "default_shipping_address",
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        address_data = validated_data.pop("default_shipping_address", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        if address_data:
            self._upsert_default_address(instance, address_data)

        return instance

    def _upsert_default_address(self, customer, data):
        address = customer.default_shipping_address
        if address is None:
            address = Address(
                customer=customer,
                first_name=customer.user.first_name,
                last_name=customer.user.last_name,
            )
        for attr, value in data.items():
            setattr(address, attr, value)
        address.is_default = True
        address.save()


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


class UserSerializer(serializers.ModelSerializer):
    """Compact user representation embedded in the login response."""

    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "groups"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )
        return attrs
