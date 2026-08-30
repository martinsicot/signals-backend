from django.urls import path
from . import views_crm

urlpatterns = [
    path("orders/", views_crm.CRMOrderListView.as_view(), name="crm-order-list"),
    path("orders/<int:order_id>/", views_crm.CRMOrderDetailView.as_view(), name="crm-order-detail"),
    path("orders/<int:order_id>/status/", views_crm.CRMOrderStatusView.as_view(), name="crm-order-status"),
]
