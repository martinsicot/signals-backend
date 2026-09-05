from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    # JWT auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API — customer-facing
    path("api/", include("accounts.api.urls")),
    path("api/", include("catalog.api.urls")),
    path("api/", include("orders.api.urls")),
    path("api/", include("cart.api.urls")),
    # API — CRM / ops
    path("api/crm/", include("accounts.api.urls_crm")),
    path("api/crm/", include("orders.api.urls_crm")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    # Serve product images from MEDIA_ROOT during local development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
