from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from orders.domain.exceptions import EmptyOrderError, OrderTooLargeError
from tests.factories import (
    CustomerFactory,
    OrderFactory,
    OrderLineFactory,
    ProductVariantFactory,
)


def make_mock_order_model():
    order = MagicMock()
    order.id = 1
    order.status = "pending"
    order.shipping_fee = Decimal("9.90")
    order.shipping_address_snapshot = {"city": "Paris"}
    order.created_at.isoformat.return_value = "2025-01-01T00:00:00"
    line = MagicMock()
    line.id = 1
    line.product_id = 1  # OrderLineModel FK column to ProductVariant
    line.product_name_snapshot = "Stop Sign"
    line.quantity = 2
    line.unit_price = Decimal("50.00")
    line.total = Decimal("100.00")
    order.lines.all.return_value = [line]
    return order


# ---------------------------------------------------------------------------
# Create order
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateOrderView:
    url = "/api/orders/"

    def test_returns_201_for_valid_guest_order(self, client):
        mock_order = make_mock_order_model()
        with patch("orders.api.views.OrderService") as MockService, \
             patch("orders.api.views.OrderModel.objects") as mock_manager:
            MockService.return_value.create_order.return_value = MagicMock(id=1)
            mock_manager.prefetch_related.return_value.get.return_value = mock_order

            response = client.post(self.url, data={
                "items": [{"variant_id": 1, "quantity": 2}],
                "shipping_address": {"city": "Paris"},
                "guest_email": "guest@example.com",
            }, content_type="application/json")

        assert response.status_code == 201

    def test_returns_422_when_order_exceeds_max_quantity(self, client):
        with patch("orders.api.views.OrderService") as MockService:
            MockService.return_value.create_order.side_effect = OrderTooLargeError(
                quantity=60, max_quantity=50
            )

            response = client.post(self.url, data={
                "items": [{"variant_id": 1, "quantity": 60}],
                "shipping_address": {},
                "guest_email": "guest@example.com",
            }, content_type="application/json")

        assert response.status_code == 422
        assert response.json()["code"] == "order_too_large"

    def test_returns_400_when_items_list_is_empty(self, client):
        response = client.post(self.url, data={
            "items": [],
            "shipping_address": {},
            "guest_email": "g@example.com",
        }, content_type="application/json")

        assert response.status_code == 400

    def test_returns_400_when_guest_email_missing_for_unauthenticated(self, client):
        response = client.post(self.url, data={
            "items": [{"variant_id": 1, "quantity": 1}],
            "shipping_address": {},
        }, content_type="application/json")

        assert response.status_code == 400
        assert "guest_email" in response.json()

    def test_uses_customer_id_when_authenticated(self, authenticated_client, test_user):
        mock_order = make_mock_order_model()
        with patch("orders.api.views.OrderService") as MockService, \
             patch("orders.api.views.OrderModel.objects") as mock_manager:
            mock_service = MockService.return_value
            mock_service.create_order.return_value = MagicMock(id=1)
            mock_manager.prefetch_related.return_value.get.return_value = mock_order

            authenticated_client.post(self.url, data={
                "items": [{"variant_id": 1, "quantity": 1}],
                "shipping_address": {},
            }, content_type="application/json")

        assert mock_service.create_order.call_args[1]["customer_id"] == test_user.customer.id


# ---------------------------------------------------------------------------
# Customer order list
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCustomerOrderListView:
    url = "/api/orders/mine/"

    def test_returns_own_orders(self, client, customer):
        OrderFactory(customer=customer)
        OrderFactory(customer=customer)
        client.force_login(customer.user)

        response = client.get(self.url)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_does_not_return_other_customer_orders(self, client, customer):
        other_customer = CustomerFactory()
        OrderFactory(customer=other_customer)
        client.force_login(customer.user)

        response = client.get(self.url)
        assert response.json() == []

    def test_returns_401_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Customer order detail
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOrderDetailView:
    def test_returns_order_for_owner(self, client, customer):
        order = OrderFactory(customer=customer)
        client.force_login(customer.user)

        response = client.get(f"/api/orders/{order.pk}/")
        assert response.status_code == 200
        assert response.json()["id"] == order.pk

    def test_returns_404_for_other_customer_order(self, client, customer):
        other_order = OrderFactory(customer=CustomerFactory())
        client.force_login(customer.user)

        response = client.get(f"/api/orders/{other_order.pk}/")
        assert response.status_code == 404

    def test_returns_401_when_unauthenticated(self, client):
        order = OrderFactory()
        response = client.get(f"/api/orders/{order.pk}/")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Order lines in response
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOrderLinesInResponse:
    def test_order_detail_includes_lines(self, client, customer):
        order = OrderFactory(customer=customer)
        variant = ProductVariantFactory()
        OrderLineFactory(order=order, product=variant, quantity=3)
        client.force_login(customer.user)

        response = client.get(f"/api/orders/{order.pk}/")
        assert response.status_code == 200
        lines = response.json()["lines"]
        assert len(lines) == 1
        assert lines[0]["quantity"] == 3
