from rest_framework import serializers
from ..models import OrderModel, OrderLineModel


class OrderLineSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderLineModel
        fields = ["id", "product", "product_name_snapshot", "quantity", "unit_price", "total"]

    def get_total(self, obj):
        return str(obj.total)


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderModel
        fields = [
            "id", "status", "lines", "shipping_fee",
            "subtotal", "total", "shipping_address_snapshot", "created_at",
        ]

    def get_subtotal(self, obj):
        return str(sum(line.total for line in obj.lines.all()))

    def get_total(self, obj):
        return str(sum(line.total for line in obj.lines.all()) + obj.shipping_fee)


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
