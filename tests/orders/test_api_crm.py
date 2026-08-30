import pytest

from orders.models import OrderModel
from tests.factories import CustomerFactory, GuestOrderFactory, OrderFactory


# ---------------------------------------------------------------------------
# CRM — Order list
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMOrderListView:
    url = "/api/crm/orders/"

    def test_returns_all_orders_for_crm(self, crm_client):
        OrderFactory()
        OrderFactory()

        response = crm_client.get(self.url)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_accessible_by_ops(self, ops_client):
        response = ops_client.get(self.url)
        assert response.status_code == 200

    def test_filters_by_status(self, crm_client):
        OrderFactory(status=OrderModel.Status.PAID)
        OrderFactory(status=OrderModel.Status.PENDING)

        response = crm_client.get(self.url, {"status": "paid"})
        assert response.status_code == 200
        assert all(o["status"] == "paid" for o in response.json())

    def test_filters_by_customer_id(self, crm_client):
        target = OrderFactory()
        OrderFactory()

        response = crm_client.get(self.url, {"customer_id": target.customer.pk})
        data = response.json()
        assert all(o["id"] == target.pk for o in data)

    def test_filters_guest_orders_by_email(self, crm_client):
        guest_order = GuestOrderFactory()
        GuestOrderFactory()

        response = crm_client.get(self.url, {"guest_email": guest_order.guest_email})
        assert response.status_code == 200
        assert any(o["id"] == guest_order.pk for o in response.json())

    def test_returns_403_for_customers(self, authenticated_client):
        response = authenticated_client.get(self.url)
        assert response.status_code == 403

    def test_returns_403_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# CRM — Order detail
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMOrderDetailView:
    def test_returns_any_order(self, crm_client):
        order = OrderFactory()

        response = crm_client.get(f"/api/crm/orders/{order.pk}/")
        assert response.status_code == 200
        assert response.json()["id"] == order.pk

    def test_returns_404_for_unknown_order(self, crm_client):
        response = crm_client.get("/api/crm/orders/99999/")
        assert response.status_code == 404

    def test_ops_can_read_order(self, ops_client):
        order = OrderFactory()
        response = ops_client.get(f"/api/crm/orders/{order.pk}/")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# CRM — Order status transitions
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMOrderStatusView:
    def _url(self, order):
        return f"/api/crm/orders/{order.pk}/status/"

    def test_transitions_paid_to_in_production(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.PAID)

        response = crm_client.patch(
            self._url(order),
            data={"status": "in_production"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_production"

    def test_transitions_in_production_to_shipped(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.IN_PRODUCTION)

        response = crm_client.patch(
            self._url(order),
            data={"status": "shipped"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "shipped"

    def test_transitions_shipped_to_delivered(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.SHIPPED)

        response = crm_client.patch(
            self._url(order),
            data={"status": "delivered"},
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_cancels_paid_order(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.PAID)

        response = crm_client.patch(
            self._url(order),
            data={"status": "cancelled"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_returns_422_for_invalid_transition(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.PENDING)

        response = crm_client.patch(
            self._url(order),
            data={"status": "delivered"},
            content_type="application/json",
        )
        assert response.status_code == 422
        assert "allowed" in response.json()

    def test_returns_422_for_backward_transition(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.SHIPPED)

        response = crm_client.patch(
            self._url(order),
            data={"status": "paid"},
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_returns_400_when_status_field_missing(self, crm_client):
        order = OrderFactory(status=OrderModel.Status.PAID)

        response = crm_client.patch(
            self._url(order),
            data={},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_ops_cannot_update_status(self, ops_client):
        order = OrderFactory(status=OrderModel.Status.PAID)

        response = ops_client.patch(
            self._url(order),
            data={"status": "in_production"},
            content_type="application/json",
        )
        assert response.status_code == 403
