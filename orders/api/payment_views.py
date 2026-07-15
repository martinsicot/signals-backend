from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from ..services.payment_service import PaymentService
from notifications.tasks import send_payment_confirmation


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        success_url = request.data.get(
            "success_url",
            f"{request.scheme}://{request.get_host()}/order/{order_id}/confirmation",
        )
        cancel_url = request.data.get(
            "cancel_url",
            f"{request.scheme}://{request.get_host()}/cart",
        )

        service = PaymentService()
        try:
            checkout_url = service.create_checkout_session(
                order_id=order_id,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"checkout_url": checkout_url})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        service = PaymentService()

        try:
            event_type = service.handle_webhook(
                payload=request.body,
                sig_header=sig_header,
            )
        except ValueError:
            return Response({"error": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        if event_type == "checkout.session.completed":
            from ..models import OrderModel
            import json
            body = json.loads(request.body)
            order_id = int(body["data"]["object"].get("metadata", {}).get("order_id", 0))
            if order_id:
                send_payment_confirmation.delay(order_id)

        return Response({"status": "ok"})
