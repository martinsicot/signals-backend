from decimal import Decimal
from ..models import Category, Product, ProductVariant


class ProductRepository:
    # --- Product (family) ---

    def get_product_by_slug(self, slug: str) -> Product:
        return (
            Product.objects
            .prefetch_related("categories", "variants__attributes__attribute")
            .get(slug=slug, is_active=True)
        )

    def list_active_products(self, category_slug: str | None = None, q: str | None = None):
        qs = (
            Product.objects
            .filter(is_active=True)
            .prefetch_related("categories", "variants")
        )
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(description__icontains=q)
        return qs

    # --- ProductVariant ---

    def get_variant_by_id(self, variant_id: int) -> ProductVariant:
        return (
            ProductVariant.objects
            .select_related("product")
            .prefetch_related("product__categories", "attributes__attribute")
            .get(id=variant_id, is_active=True)
        )

    def get_variant_by_sku(self, sku: str) -> ProductVariant:
        return (
            ProductVariant.objects
            .select_related("product")
            .prefetch_related("product__categories", "attributes__attribute")
            .get(sku=sku, is_active=True)
        )

    def get_variant_price(self, variant_id: int) -> Decimal:
        return ProductVariant.objects.values_list("price", flat=True).get(
            id=variant_id, is_active=True
        )

    def list_active_variants_by_ids(self, ids: list[int]):
        return (
            ProductVariant.objects
            .filter(id__in=ids, is_active=True)
            .select_related("product")
        )

    # --- Category ---

    def get_category_by_slug(self, slug: str) -> Category:
        return Category.objects.get(slug=slug)

    # --- Legacy shims (used by cart and order_service) ---

    def get_by_id(self, variant_id: int) -> ProductVariant:
        return self.get_variant_by_id(variant_id)

    def get_price(self, variant_id: int) -> Decimal:
        return self.get_variant_price(variant_id)

    def list_active(self, category_slug: str | None = None, q: str | None = None):
        return self.list_active_products(category_slug=category_slug, q=q)
