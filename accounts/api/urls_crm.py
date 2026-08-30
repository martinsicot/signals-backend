from django.urls import path
from . import views_crm

urlpatterns = [
    path("customers/", views_crm.CRMCustomerListView.as_view(), name="crm-customer-list"),
    path("customers/<int:customer_id>/", views_crm.CRMCustomerDetailView.as_view(), name="crm-customer-detail"),
    path("customers/<int:customer_id>/addresses/", views_crm.CRMAddressListView.as_view(), name="crm-address-list"),
    path("customers/<int:customer_id>/addresses/<int:address_id>/", views_crm.CRMAddressDetailView.as_view(), name="crm-address-detail"),
]
