from decimal import Decimal
from django.conf import settings
from rest_framework import serializers
from ..models import OrderModel, OrderLineModel


def _ttc(amount):
    return round(amount * (Decimal("1") + settings.VAT_RATE), 2)


class OrderLineSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    total_ttc = serializers.SerializerMethodField()

    class Meta:
        model = OrderLineModel
        fields = ["id", "product", "product_name_snapshot", "quantity", "unit_price", "total", "total_ttc"]

    def get_total(self, obj):
        return str(obj.total)

    def get_total_ttc(self, obj):
        return str(_ttc(obj.total))


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    subtotal_ttc = serializers.SerializerMethodField()
    total_ttc = serializers.SerializerMethodField()
    vat_rate = serializers.SerializerMethodField()

    class Meta:
        model = OrderModel
        fields = [
            "id", "status", "lines", "shipping_fee",
            "subtotal", "total", "subtotal_ttc", "total_ttc", "vat_rate",
            "shipping_address_snapshot", "created_at",
        ]

    def get_subtotal(self, obj):
        return str(sum(line.total for line in obj.lines.all()))

    def get_total(self, obj):
        return str(sum(line.total for line in obj.lines.all()) + obj.shipping_fee)

    def get_subtotal_ttc(self, obj):
        return str(_ttc(sum(line.total for line in obj.lines.all())))

    def get_total_ttc(self, obj):
        return str(_ttc(sum(line.total for line in obj.lines.all()) + obj.shipping_fee))

    def get_vat_rate(self, obj):
        return str(settings.VAT_RATE)


class OrderStatusSerializer(serializers.ModelSerializer):
    lines_summary = serializers.SerializerMethodField()
    total_ttc = serializers.SerializerMethodField()

    class Meta:
        model = OrderModel
        fields = ["id", "status", "guest_email", "lines_summary", "total_ttc"]

    def get_lines_summary(self, obj):
        return [
            {"name": line.product_name_snapshot, "quantity": line.quantity}
            for line in obj.lines.all()
        ]

    def get_total_ttc(self, obj):
        subtotal = sum(line.total for line in obj.lines.all())
        return str(_ttc(subtotal + obj.shipping_fee))


class CreateOrderSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField(), min_length=1)
    shipping_address = serializers.DictField()
    guest_email = serializers.EmailField(required=False, allow_blank=True)

    def validate_items(self, items):
        for item in items:
            if "variant_id" not in item:
                raise serializers.ValidationError("Each item must have a variant_id.")
            if "quantity" not in item or int(item["quantity"]) < 1:
                raise serializers.ValidationError("Each item must have a quantity >= 1.")
        return items
