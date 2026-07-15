from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from ..models import Category, Product
from ..repositories.product_repository import ProductRepository
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer

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
        products = product_repo.list_active(category_slug=category_slug)
        return Response(ProductListSerializer(products, many=True).data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.select_related("category").get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailSerializer(product).data)
