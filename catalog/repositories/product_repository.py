from decimal import Decimal
from ..models import Product, Category


class ProductRepository:
    def get_by_id(self, product_id: int) -> Product:
        return Product.objects.select_related("category").get(id=product_id, is_active=True)

    def get_price(self, product_id: int) -> Decimal:
        return Product.objects.values_list("price", flat=True).get(id=product_id, is_active=True)

    def list_active(self, category_slug: str | None = None, q: str | None = None):
        qs = Product.objects.filter(is_active=True).select_related("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(description__icontains=q)
        return qs

    def get_category_by_slug(self, slug: str) -> Category:
        return Category.objects.get(slug=slug)
