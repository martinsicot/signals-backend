from rest_framework import serializers
from ..models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "meta_title", "meta_description"]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category_name", "price", "image", "dimensions", "material"]


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "category", "description",
            "price", "weight_kg", "dimensions", "material", "image",
            "meta_title", "meta_description", "created_at",
        ]
