from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ProductSitemap, CategorySitemap

sitemaps = {"products": ProductSitemap, "categories": CategorySitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/", include("accounts.api.urls")),
    path("api/", include("catalog.api.urls")),
    path("api/", include("orders.api.urls")),
    path("api/", include("cart.api.urls")),
    # Web templates
    path("", include("pages.urls")),
    path("", include("catalog.urls_web")),
    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
