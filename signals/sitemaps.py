from django.contrib.sitemaps import Sitemap
from catalog.models import Product, Category


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return f"/produits/{obj.slug}/"

    def lastmod(self, obj):
        return obj.created_at


class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return f"/catalogue/{obj.slug}/"
