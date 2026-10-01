from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import fields as f, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from ..cart import Cart
from orders.domain.rules import compute_shipping_fee


_CartResponseSerializer = inline_serializer(
    name="CartResponse",
    fields={
        "items": f.ListField(),
        "item_count": f.IntegerField(),
        "subtotal": f.CharField(),
        "shipping_fee": f.CharField(),
        "total": f.CharField(),
    },
)
_ItemCountSerializer = inline_serializer(
    name="ItemCount",
    fields={"item_count": f.IntegerField()},
)


class CartView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: _CartResponseSerializer})
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

    @extend_schema(
        request=inline_serializer(
            name="CartAddRequest",
            fields={"variant_id": f.IntegerField(), "quantity": f.IntegerField(required=False)},
        ),
        responses={200: _ItemCountSerializer},
    )
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

    @extend_schema(
        request=inline_serializer(name="CartUpdateRequest", fields={"quantity": f.IntegerField()}),
        responses={200: _ItemCountSerializer},
    )
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

    @extend_schema(responses={204: None})
    def delete(self, request, variant_id):
        Cart(request).remove(variant_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={204: None})
    def delete(self, request):
        Cart(request).clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
