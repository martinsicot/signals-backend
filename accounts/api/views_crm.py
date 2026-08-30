from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Customer, Address
from ..permissions import IsCRM, IsCRMOrOps
from .serializers import CustomerSerializer, AddressSerializer

User = get_user_model()


class CRMCustomerListView(APIView):
    """List all customers or search by email."""

    permission_classes = [IsCRMOrOps]

    def get(self, request):
        qs = Customer.objects.select_related("user").prefetch_related("addresses")
        email = request.query_params.get("email")
        if email:
            qs = qs.filter(user__email__icontains=email)
        return Response(CustomerSerializer(qs, many=True).data)


class CRMCustomerDetailView(APIView):
    """Read a single customer's profile."""

    permission_classes = [IsCRMOrOps]

    def get(self, request, customer_id):
        customer = get_object_or_404(
            Customer.objects.select_related("user").prefetch_related("addresses"),
            pk=customer_id,
        )
        return Response(CustomerSerializer(customer).data)


class CRMAddressListView(APIView):
    """List or create addresses for any customer."""

    permission_classes = [IsCRM]

    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        addresses = customer.addresses.all()
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        serializer = AddressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        address = serializer.save(customer=customer)
        return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED)


class CRMAddressDetailView(APIView):
    """Read, update or delete a specific address."""

    permission_classes = [IsCRM]

    def _get_address(self, customer_id, address_id):
        return get_object_or_404(Address, pk=address_id, customer_id=customer_id)

    def get(self, request, customer_id, address_id):
        address = self._get_address(customer_id, address_id)
        return Response(AddressSerializer(address).data)

    def patch(self, request, customer_id, address_id):
        address = self._get_address(customer_id, address_id)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, customer_id, address_id):
        address = self._get_address(customer_id, address_id)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
