from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import OrderModel
from .serializers import OrderSerializer
from accounts.permissions import IsCRMOrOps, IsCRM


ALLOWED_STATUS_TRANSITIONS = {
    OrderModel.Status.PAID: [OrderModel.Status.IN_PRODUCTION, OrderModel.Status.CANCELLED],
    OrderModel.Status.IN_PRODUCTION: [OrderModel.Status.SHIPPED, OrderModel.Status.CANCELLED],
    OrderModel.Status.SHIPPED: [OrderModel.Status.DELIVERED],
}


class CRMOrderListView(APIView):
    """
    List all orders with optional filters.
    Query params: status, customer_id, guest_email
    """

    permission_classes = [IsCRMOrOps]

    def get(self, request):
        qs = OrderModel.objects.prefetch_related("lines").select_related("customer__user")

        if s := request.query_params.get("status"):
            qs = qs.filter(status=s)
        if customer_id := request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=customer_id)
        if guest_email := request.query_params.get("guest_email"):
            qs = qs.filter(guest_email__icontains=guest_email)

        return Response(OrderSerializer(qs, many=True).data)


class CRMOrderDetailView(APIView):
    """Read a single order."""

    permission_classes = [IsCRMOrOps]

    def get(self, request, order_id):
        order = get_object_or_404(
            OrderModel.objects.prefetch_related("lines").select_related("customer__user"),
            pk=order_id,
        )
        return Response(OrderSerializer(order).data)


class CRMOrderStatusView(APIView):
    """
    Update order status following the allowed transition graph.
    Only CRM members can change status (ops is read-only on orders).
    """

    permission_classes = [IsCRM]

    def patch(self, request, order_id):
        order = get_object_or_404(OrderModel, pk=order_id)
        new_status = request.data.get("status")

        if not new_status:
            return Response({"status": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            return Response(
                {
                    "error": f"Cannot transition from '{order.status}' to '{new_status}'.",
                    "allowed": allowed,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)
