"""
Tests Stripe webhook — ticket TEST-007.

Couvre les 8 cas définis dans todo/TEST-007-stripe-webhook-tests.md :
  1. checkout.session.completed → commande PAID, email envoyé
  2. checkout.session.expired   → commande CANCELLED
  3. payment_intent.payment_failed → commande CANCELLED
  4. Signature invalide          → 400, rien en base
  5. Event inconnu               → 200, ignore silencieusement
  6. Commande introuvable        → pas de crash, 200
  7. Idempotence (webhook reçu 2×) → email envoyé une seule fois
  8. Commande déjà PAID          → ne re-déclenche pas les notifications

Stripe n'est jamais appelé pour de vrai : stripe.Webhook.construct_event est
patché via unittest.mock.patch. La tâche Celery est également patchée.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from orders.models import OrderModel
from tests.factories import OrderFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEBHOOK_URL = "/api/webhooks/stripe/"


def _post_webhook(client, payload: bytes, sig: str = "valid-sig"):
    return client.post(
        WEBHOOK_URL,
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=sig,
    )


def _webhook_payload(event_type: str, order_id: int) -> bytes:
    """Build a minimal raw Stripe-like JSON payload."""
    return json.dumps({
        "type": event_type,
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)},
            }
        },
    }).encode()


def _make_event(event_type: str, order_id: int) -> dict:
    """
    Build a mock event dict where data.object uses attribute-style access
    (mimics how the Stripe Python SDK exposes nested objects).
    """
    obj = MagicMock()
    obj.metadata = {"order_id": str(order_id)}
    return {"type": event_type, "data": {"object": obj}}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStripeWebhook:

    # -------------------------------------------------------------------
    # Cas 1 : checkout.session.completed → PAID + email
    # -------------------------------------------------------------------

    def test_checkout_completed_marks_order_paid(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_event.return_value = _make_event("checkout.session.completed", order.pk)
            mock_task.delay = MagicMock()

            response = _post_webhook(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.PAID

    def test_checkout_completed_sends_confirmation_email(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_event.return_value = _make_event("checkout.session.completed", order.pk)
            mock_task.delay = MagicMock()

            _post_webhook(client, payload)

        mock_task.delay.assert_called_once_with(order.pk)

    # -------------------------------------------------------------------
    # Cas 2 : checkout.session.expired → CANCELLED
    # -------------------------------------------------------------------

    def test_session_expired_cancels_order(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.expired", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation"):
            mock_event.return_value = _make_event("checkout.session.expired", order.pk)

            response = _post_webhook(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.CANCELLED

    # -------------------------------------------------------------------
    # Cas 3 : payment_intent.payment_failed → CANCELLED
    # -------------------------------------------------------------------

    def test_payment_failed_cancels_order(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("payment_intent.payment_failed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation"):
            mock_event.return_value = _make_event("payment_intent.payment_failed", order.pk)

            response = _post_webhook(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.CANCELLED

    # -------------------------------------------------------------------
    # Cas 4 : Signature invalide → 400, rien en base
    # -------------------------------------------------------------------

    def test_invalid_signature_returns_400(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event:
            mock_event.side_effect = ValueError("Invalid signature")

            response = _post_webhook(client, payload, sig="tampered-sig")

        assert response.status_code == 400
        assert "error" in response.json()

    def test_invalid_signature_does_not_change_order_status(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event:
            mock_event.side_effect = ValueError("Invalid signature")
            _post_webhook(client, payload, sig="tampered-sig")

        order.refresh_from_db()
        assert order.status == OrderModel.Status.PENDING

    # -------------------------------------------------------------------
    # Cas 5 : Event inconnu → 200, ignore silencieusement
    # -------------------------------------------------------------------

    def test_unknown_event_type_returns_200(self, client):
        order = OrderFactory()
        payload = _webhook_payload("customer.subscription.created", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation"):
            # construct_event retourne le payload brut (dict JSON) — simulé ici
            mock_event.return_value = json.loads(payload)

            response = _post_webhook(client, payload)

        assert response.status_code == 200

    def test_unknown_event_type_does_not_change_order_status(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("customer.subscription.created", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)
            _post_webhook(client, payload)

        order.refresh_from_db()
        assert order.status == OrderModel.Status.PENDING

    # -------------------------------------------------------------------
    # Cas 6 : Commande introuvable → pas de crash
    # -------------------------------------------------------------------

    def test_missing_order_id_in_metadata_does_not_crash(self, client):
        """Webhook avec metadata vide → le service retourne silencieusement."""
        payload = json.dumps({
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {}}},
        }).encode()

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation"):
            mock_event.return_value = json.loads(payload)

            response = _post_webhook(client, payload)

        assert response.status_code == 200

    def test_nonexistent_order_id_does_not_crash(self, client):
        """order_id valide en metadata mais inexistant en base → pas de crash."""
        payload = _webhook_payload("checkout.session.completed", order_id=99999)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_event.return_value = _make_event("checkout.session.completed", order_id=99999)
            mock_task.delay = MagicMock()

            # Le repo fait un .update() sur un queryset vide : ne lève pas d'exception
            response = _post_webhook(client, payload)

        assert response.status_code == 200
        mock_task.delay.assert_not_called()

    # -------------------------------------------------------------------
    # Cas 7 : Idempotence — webhook reçu deux fois
    # -------------------------------------------------------------------

    def test_webhook_received_twice_sends_email_only_once(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_task.delay = MagicMock()
            mock_event.return_value = _make_event("checkout.session.completed", order.pk)

            _post_webhook(client, payload)
            _post_webhook(client, payload)

        mock_task.delay.assert_called_once_with(order.pk)

    def test_webhook_received_twice_order_stays_paid(self, client):
        order = OrderFactory(status=OrderModel.Status.PENDING)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_task.delay = MagicMock()
            mock_event.return_value = _make_event("checkout.session.completed", order.pk)

            _post_webhook(client, payload)
            _post_webhook(client, payload)

        order.refresh_from_db()
        assert order.status == OrderModel.Status.PAID

    # -------------------------------------------------------------------
    # Cas 8 : Commande déjà PAID → ne re-déclenche pas les notifications
    # -------------------------------------------------------------------

    def test_already_paid_order_does_not_trigger_email(self, client):
        order = OrderFactory(status=OrderModel.Status.PAID)
        payload = _webhook_payload("checkout.session.completed", order.pk)

        with patch("orders.services.payment_service.stripe.Webhook.construct_event") as mock_event, \
             patch("notifications.tasks.send_payment_confirmation") as mock_task:
            mock_task.delay = MagicMock()
            mock_event.return_value = _make_event("checkout.session.completed", order.pk)

            response = _post_webhook(client, payload)

        order.refresh_from_db()
        assert response.status_code == 200
        assert order.status == OrderModel.Status.PAID
        mock_task.delay.assert_not_called()
