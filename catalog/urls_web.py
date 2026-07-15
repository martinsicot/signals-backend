from django.urls import path
from .views_web import ProductListView, ProductDetailView

urlpatterns = [
    path("catalogue/", ProductListView.as_view(), name="product-list-web"),
    path("catalogue/<slug:category_slug>/", ProductListView.as_view(), name="category-detail-web"),
    path("produits/<slug:slug>/", ProductDetailView.as_view(), name="product-detail-web"),
]
