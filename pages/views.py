from django.views.generic import TemplateView
from catalog.models import Category, Product


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["featured_products"] = Product.objects.filter(is_active=True).select_related("category")[:6]
        return ctx


class CGVView(TemplateView):
    template_name = "pages/cgv.html"


class MentionsLegalesView(TemplateView):
    template_name = "pages/mentions_legales.html"
