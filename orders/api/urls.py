from django.urls import path
from . import views, payment_views

urlpatterns = [
    path("orders/", views.CreateOrderView.as_view(), name="order-create"),
    path("orders/mine/", views.CustomerOrderListView.as_view(), name="order-list"),
    path("orders/<int:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:order_id>/checkout/", payment_views.CreateCheckoutSessionView.as_view(), name="order-checkout"),
    path("webhooks/stripe/", payment_views.StripeWebhookView.as_view(), name="stripe-webhook"),
]
