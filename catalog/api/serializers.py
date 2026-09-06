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


def _absolute(request, url):
    """Absolute URL for a MEDIA-relative path, when a request is available."""
    if not url:
        return None
    return request.build_absolute_uri(url) if request else url


class ProductListSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "base_code", "type", "categories",
                  "image", "thumbnail", "min_price", "is_active"]

    def get_categories(self, obj):
        return [{"id": c.id, "name": c.name, "slug": c.slug} for c in obj.categories.all()]

    def get_min_price(self, obj):
        prices = [v.price for v in obj.variants.all() if v.price is not None]
        return str(min(prices)) if prices else None

    def get_thumbnail(self, obj):
        """240px WebP thumbnail for catalog grids."""
        return _absolute(self.context.get("request"), obj.thumbnail_url(240))


class ProductDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    thumbnail_lg = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "base_code", "type", "categories",
            "description", "image", "thumbnail", "thumbnail_lg", "is_active",
            "meta_title", "meta_description",
            "variants",
        ]

    def get_thumbnail(self, obj):
        """240px WebP thumbnail."""
        return _absolute(self.context.get("request"), obj.thumbnail_url(240))

    def get_thumbnail_lg(self, obj):
        """480px WebP thumbnail (retina for ~320px display)."""
        return _absolute(self.context.get("request"), obj.thumbnail_url(480))


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "price", "weight_kg", "is_active", "product_name", "product_slug", "attributes"]
