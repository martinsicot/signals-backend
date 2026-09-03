from rest_framework import serializers
from ..models import Category, Product, ProductVariant, AttributeValue


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "meta_title", "meta_description"]


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_slug = serializers.CharField(source="attribute.slug", read_only=True)
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = ["id", "attribute_slug", "attribute_name", "value", "display"]


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "price", "weight_kg", "is_active", "attributes"]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "base_code", "type", "category_name", "image", "min_price", "is_active"]

    def get_min_price(self, obj):
        prices = [v.price for v in obj.variants.all() if v.price is not None]
        return str(min(prices)) if prices else None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "base_code", "type", "category",
            "description", "image", "is_active",
            "meta_title", "meta_description",
            "variants",
        ]


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "price", "weight_kg", "is_active", "product_name", "product_slug", "attributes"]
