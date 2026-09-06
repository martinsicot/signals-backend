from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.db.models import Count
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
        shape = request.query_params.get("shape") or None
        classe = request.query_params.get("classe") or None
        products = product_repo.list_active_products(
            category_slug=category_slug, q=q, shape=shape, classe=classe
        )

        paginator = PageNumberPagination()
        paginator.page_size = 24  # grille 4×6, plus naturel que 20
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ProductFiltersView(APIView):
    permission_classes = [AllowAny]

    SHAPE_LABELS = {
        "triangle": "Danger",
        "round": "Ordre",
        "square": "Indication",
        "directional": "Direction",
        "rect": "Localisation",
    }

    def get(self, request):
        shapes = (
            Product.objects
            .filter(is_active=True)
            .exclude(shape="unknown")
            .values("shape")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "shapes": [
                {
                    "value": s["shape"],
                    "label": self.SHAPE_LABELS.get(s["shape"], s["shape"]),
                    "count": s["count"],
                }
                for s in shapes
                if s["shape"] in self.SHAPE_LABELS
            ],
            "classes": [
                {"value": "CL1", "label": "Classe 1"},
                {"value": "CL2", "label": "Classe 2"},
            ],
        })


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
