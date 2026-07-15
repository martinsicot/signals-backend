from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from ..services.order_service import OrderService
from ..domain.exceptions import EmptyOrderError, OrderTooLargeError, ProductNotAvailableError
from ..models import OrderModel
from .serializers import OrderSerializer, CreateOrderSerializer


class CreateOrderView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        customer_id = None
        guest_email = data.get("guest_email", "")

        if request.user.is_authenticated:
            customer_id = request.user.customer.id
        elif not guest_email:
            return Response(
                {"guest_email": ["Required for guest checkout."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = OrderService()
        try:
            order = service.create_order(
                cart_items=data["items"],
                shipping_address=data["shipping_address"],
                customer_id=customer_id,
                guest_email=guest_email,
            )
        except OrderTooLargeError as e:
            return Response(
                {"error": str(e), "code": "order_too_large"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except EmptyOrderError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProductNotAvailableError as e:
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        order_model = OrderModel.objects.prefetch_related("lines").get(id=order.id)
        return Response(OrderSerializer(order_model).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = OrderModel.objects.prefetch_related("lines").get(
                id=order_id,
                customer=request.user.customer,
            )
        except OrderModel.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class CustomerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            OrderModel.objects
            .filter(customer=request.user.customer)
            .prefetch_related("lines")
            .order_by("-created_at")
        )
        return Response(OrderSerializer(orders, many=True).data)
