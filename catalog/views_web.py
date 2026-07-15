from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Product, Category


class ProductListView(ListView):
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related("category").order_by("name")
        slug = self.kwargs.get("category_slug")
        if slug:
            self.current_category = get_object_or_404(Category, slug=slug)
            qs = qs.filter(category=self.current_category)
        else:
            self.current_category = None
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["current_category"] = self.current_category
        return ctx


class ProductDetailView(DetailView):
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related("category")
