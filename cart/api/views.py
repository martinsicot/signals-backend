from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.conf import settings
from ..cart import Cart
from orders.domain.rules import compute_shipping_fee


class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = Cart(request)
        items = list(cart)
        subtotal = cart.get_subtotal()
        shipping_fee = compute_shipping_fee(
            subtotal,
            free_threshold=settings.SHIPPING_FREE_THRESHOLD,
            fee=settings.SHIPPING_FEE,
        )
        return Response({
            "items": items,
            "item_count": len(cart),
            "subtotal": str(subtotal),
            "shipping_fee": str(shipping_fee),
            "total": str(subtotal + shipping_fee),
        })


class CartAddView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        variant_id = request.data.get("variant_id")
        quantity = request.data.get("quantity", 1)

        if not variant_id:
            return Response({"error": "variant_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quantity = int(quantity)
            assert quantity >= 1
        except (ValueError, AssertionError):
            return Response({"error": "quantity must be >= 1."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart(request)
        cart.add(variant_id=int(variant_id), quantity=quantity)
        return Response({"item_count": len(cart)})


class CartUpdateView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, variant_id):
        try:
            quantity = int(request.data.get("quantity", 0))
        except (ValueError, TypeError):
            return Response({"error": "quantity must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart(request)
        if quantity <= 0:
            cart.remove(variant_id)
        else:
            cart.add(variant_id=variant_id, quantity=quantity, override_quantity=True)
        return Response({"item_count": len(cart)})


class CartRemoveView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, variant_id):
        Cart(request).remove(variant_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        Cart(request).clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
