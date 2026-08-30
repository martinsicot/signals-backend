from django.urls import path
from .views_web import CheckoutView, OrderConfirmationView, OrderListView, OrderDetailView

urlpatterns = [
    path("commande/", CheckoutView.as_view(), name="checkout"),
    path("mes-commandes/", OrderListView.as_view(), name="order-list"),
    path("mes-commandes/<int:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("mes-commandes/<int:order_id>/confirmation/", OrderConfirmationView.as_view(), name="order-confirmation"),
]
