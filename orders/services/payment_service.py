import stripe
from django.conf import settings
from ..repositories.order_repository import OrderRepository
from ..domain.entities import OrderStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self):
        self.order_repo = OrderRepository()

    def create_checkout_session(self, order_id: int, success_url: str, cancel_url: str) -> str:
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
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"order_id": str(order_id)},
            customer_email=order.guest_email or None,
        )

        self.order_repo.update_stripe_session(order_id, session.id)
        return session.url

    def handle_webhook(self, payload: bytes, sig_header: str) -> str | None:
        """Process a Stripe webhook event. Returns the event type handled."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")

        event_type = event["type"]
        obj = event["data"]["object"]
        order_id = int(obj.get("metadata", {}).get("order_id", 0))

        if not order_id:
            return None

        if event_type == "checkout.session.completed":
            self.order_repo.update_status(order_id, OrderStatus.PAID)
            return event_type

        if event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
            self.order_repo.update_status(order_id, OrderStatus.CANCELLED)
            return event_type

        return None
