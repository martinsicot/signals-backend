from django.urls import path
from .views_web import CartView, CartAddView, CartUpdateView, CartRemoveView

urlpatterns = [
    path("panier/", CartView.as_view(), name="cart"),
    path("panier/ajouter/", CartAddView.as_view(), name="cart-add-web"),
    path("panier/modifier/<int:product_id>/", CartUpdateView.as_view(), name="cart-update-web"),
    path("panier/supprimer/<int:product_id>/", CartRemoveView.as_view(), name="cart-remove-web"),
]
