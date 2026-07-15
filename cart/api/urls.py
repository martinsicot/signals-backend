from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.CartView.as_view(), name="cart-detail"),
    path("cart/add/", views.CartAddView.as_view(), name="cart-add"),
    path("cart/update/<int:product_id>/", views.CartUpdateView.as_view(), name="cart-update"),
    path("cart/remove/<int:product_id>/", views.CartRemoveView.as_view(), name="cart-remove"),
    path("cart/clear/", views.CartClearView.as_view(), name="cart-clear"),
]
