import json
import stripe
from django.conf import settings
from ..repositories.order_repository import OrderRepository
from ..domain.entities import OrderStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self):
        self.order_repo = OrderRepository()

    def create_checkout_session(self, order_id: int, return_url: str) -> str:
        order = self.order_repo.get_by_id(order_id)

        line_items = [
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": line.product_name},
                    "unit_amount": int(line.unit_price * 100),
                },
                "quantity": line.quantity,
            }
            for line in order.lines
        ]

        if order.shipping_fee > 0:
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": "Frais de livraison"},
                    "unit_amount": int(order.shipping_fee * 100),
                },
                "quantity": 1,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            ui_mode="embedded_page",
            return_url=return_url,
            metadata={"order_id": str(order_id)},
            customer_email=order.guest_email or None,
        )

        self.order_repo.update_stripe_session(order_id, session.id)
        return session.client_secret

    def process_webhook(self, payload: bytes, sig_header: str) -> None:
        """Verify, route and fully handle a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")

        event_type = event["type"]
        obj = event["data"]["object"]
        try:
            order_id = int(obj.metadata["order_id"])
        except (AttributeError, KeyError, TypeError, ValueError):
            return

        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(order_id, payload)
        elif event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
            self.order_repo.update_status(order_id, OrderStatus.CANCELLED)

    def _handle_checkout_completed(self, order_id: int, payload: bytes) -> None:
        from notifications.tasks import send_payment_confirmation

        updated = self.order_repo.update_status(
            order_id, OrderStatus.PAID, only_if_not=OrderStatus.PAID
        )
        if not updated:
            return

        session_obj = json.loads(payload)["data"]["object"]
        shipping = session_obj.get("shipping_details") or {}
        if shipping:
            self.order_repo.update_shipping_snapshot(order_id, shipping)

        send_payment_confirmation.delay(order_id)
