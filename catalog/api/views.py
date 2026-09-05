from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from ..models import Category, Product, ProductVariant
from ..repositories.product_repository import ProductRepository
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductVariantDetailSerializer,
)

product_repo = ProductRepository()


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)


class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")
        q = request.query_params.get("q", "").strip() or None
        products = product_repo.list_active_products(category_slug=category_slug, q=q)
        return Response(ProductListSerializer(products, many=True, context={"request": request}).data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = product_repo.get_product_by_slug(slug)
        except Product.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)


class ProductVariantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            variant = product_repo.get_variant_by_id(pk)
        except ProductVariant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductVariantDetailSerializer(variant).data)
