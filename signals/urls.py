from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ProductSitemap, CategorySitemap

sitemaps = {"products": ProductSitemap, "categories": CategorySitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    # API — customer-facing
    path("api/", include("accounts.api.urls")),
    path("api/", include("catalog.api.urls")),
    path("api/", include("orders.api.urls")),
    path("api/", include("cart.api.urls")),
    # API — CRM / ops
    path("api/crm/", include("accounts.api.urls_crm")),
    path("api/crm/", include("orders.api.urls_crm")),
    # Web templates
    path("", include("pages.urls")),
    path("", include("catalog.urls_web")),
    path("", include("accounts.urls_web")),
    path("", include("cart.urls_web")),
    path("", include("orders.urls_web")),
    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
