from django.urls import path
from . import views

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/filters/", views.ProductFiltersView.as_view(), name="product-filters"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("variants/<int:pk>/", views.ProductVariantDetailView.as_view(), name="variant-detail"),
]
