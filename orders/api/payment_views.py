from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import fields as f, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import OrderModel
from ..services.payment_service import PaymentService
from notifications.tasks import send_payment_confirmation


class CreateCheckoutSessionView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer(
            name="CheckoutSessionRequest",
            fields={
                "return_url": f.CharField(required=False),
                "guest_email": f.EmailField(required=False),
            },
        ),
        responses={200: inline_serializer(name="CheckoutSessionResponse", fields={"client_secret": f.CharField()})},
    )
    def post(self, request, order_id):
        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_authenticated:
            if not hasattr(request.user, "customer") or order.customer_id != request.user.customer.id:
                return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_email = request.data.get("guest_email", "").strip().lower()
            if not guest_email or order.guest_email.lower() != guest_email:
                return Response(
                    {"detail": "guest_email requis et doit correspondre à la commande."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return_url = request.data.get(
            "return_url",
            f"{settings.FRONTEND_BASE_URL}/checkout/confirmation?session_id={{CHECKOUT_SESSION_ID}}",
        )

        service = PaymentService()
        try:
            client_secret = service.create_checkout_session(
                order_id=order_id,
                return_url=return_url,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"client_secret": client_secret})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        service = PaymentService()

        try:
            event_type, order_id = service.handle_webhook(
                payload=request.body,
                sig_header=sig_header,
            )
        except ValueError:
            return Response({"error": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        if event_type == "checkout.session.completed" and order_id:
            import json
            session_obj = json.loads(request.body)["data"]["object"]
            shipping = session_obj.get("shipping_details") or {}
            if shipping:
                OrderModel.objects.filter(id=order_id).update(
                    shipping_address_snapshot=shipping
                )
            send_payment_confirmation.delay(order_id)

        return Response({"status": "ok"})
