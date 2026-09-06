"""
Tests for Stripe checkout session creation and webhook handling.

Stripe is never called for real — stripe.checkout.Session.create and
stripe.Webhook.construct_event are patched at the stripe library level.
The Celery task is always patched to avoid a broker dependency.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from orders.models import OrderModel
from tests.factories import CustomerFactory, OrderFactory, OrderLineFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stripe_session(url="https://checkout.stripe.com/pay/test_session"):
    session = MagicMock()
    session.id = "cs_test_123"
    session.url = url
    return session


def _webhook_payload(event_type: str, order_id: int) -> bytes:
    return json.dumps({
        "type": event_type,
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)},
            }
        },
    }).encode()


# ---------------------------------------------------------------------------
# POST /api/orders/{id}/checkout/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateCheckoutSessionView:
    def _url(self, order_id):
        return f"/api/orders/{order_id}/checkout/"

    def test_returns_checkout_url_for_order_owner(self, client, customer):
        order = OrderFactory(customer=customer)
        OrderLineFactory(order=order)
        client.force_login(customer.user)

        with patch("orders.services.payment_service.stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = _make_stripe_session()

            response = client.post(self._url(order.pk), content_type="application/json")

        assert response.status_code == 200
        assert response.json()["checkout_url"] == "https://checkout.stripe.com/pay/test_session"

    def test_stripe_session_includes_order_metadata(self, client, customer):
        order = OrderFactory(customer=customer)
        OrderLineFactory(order=order)
        client.force_login(customer.user)

        with patch("orders.services.payment_service.stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = _make_stripe_session()
            client.post(self._url(order.pk), content_type="application/json")

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["metadata"]["order_id"] == str(order.pk)

    def test_stripe_session_includes_line_items(self, client, customer):
        order = OrderFactory(customer=customer)
        OrderLineFactory(order=order, quantity=2)
        client.force_login(customer.user)

        with patch("orders.services.payment_service.stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = _make_stripe_session()
            client.post(self._url(order.pk), content_type="application/json")

        line_items = mock_create.call_args[1]["line_items"]
        # product line + shipping fee line
        assert len(line_items) >= 1
        assert any(item["quantity"] == 2 for item in line_items)

    def test_custom_success_and_cancel_urls_are_forwarded(self, client, customer):
        order = OrderFactory(customer=customer)
        OrderLineFactory(order=order)
        client.force_login(customer.user)

        with patch("orders.services.payment_service.stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = _make_stripe_session()
            client.post(self._url(order.pk), data={
                "success_url": "https://mysite.com/success",
                "cancel_url": "https://mysite.com/cancel",
            }, content_type="application/json")

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["success_url"] == "https://mysite.com/success"
        assert call_kwargs["cancel_url"] == "https://mysite.com/cancel"

    def test_returns_400_when_stripe_raises(self, client, customer):
        order = OrderFactory(customer=customer)
        OrderLineFactory(order=order)
        client.force_login(customer.user)

        with patch("orders.services.payment_service.stripe.checkout.Session.create") as mock_create:
            mock_create.side_effect = Exception("Stripe unavailable")

            response = client.post(self._url(order.pk), content_type="application/json")

        assert response.status_code == 400
        assert "error" in response.json()

    def test_returns_401_when_unauthenticated(self, client):
        order = OrderFactory()
        response = client.post(self._url(order.pk), content_type="application/json")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/webhooks/stripe/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStripeWebhookView:
    url = "/api/webhooks/stripe/"

    def _post(self, client, payload: bytes, sig: str = "valid-sig"):
        return client.post(
            self.url,
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig,
        )

    # --- checkout.session.completed ---

    def test_marks_order_paid_on_completed_event(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation") as mock_task:
            mock_event.return_value = json.loads(payload)
            mock_task.delay = MagicMock()

            response = self._post(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.PAID

    def test_triggers_confirmation_email_on_completed_event(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation") as mock_task:
            mock_event.return_value = json.loads(payload)
            mock_task.delay = MagicMock()

            self._post(client, payload)

        mock_task.delay.assert_called_once_with(order.pk)

    # --- checkout.session.expired ---

    def test_cancels_order_on_expired_event(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.expired", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)

            response = self._post(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.CANCELLED

    # --- payment_intent.payment_failed ---

    def test_cancels_order_on_payment_failed_event(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("payment_intent.payment_failed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)

            response = self._post(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.CANCELLED

    # --- unknown event type ---

    def test_returns_200_for_unhandled_event_type(self, client):
        order = OrderFactory()
        payload = _webhook_payload("customer.created", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)

            response = self._post(client, payload)

        assert response.status_code == 200

    # --- invalid signature ---

    def test_returns_400_on_invalid_signature(self, client):
        order = OrderFactory()
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event:
            mock_event.side_effect = ValueError("Invalid signature")

            response = self._post(client, payload, sig="bad-sig")

        assert response.status_code == 400
        assert "error" in response.json()

    # --- missing order_id in metadata ---

    def test_returns_200_gracefully_when_order_id_missing(self, client):
        payload = json.dumps({
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {}}},
        }).encode()

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("orders.api.payment_views.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)

            response = self._post(client, payload)

        assert response.status_code == 200
