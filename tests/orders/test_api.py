from decimal import Decimal
from unittest.mock import patch, MagicMock
import pytest
from orders.domain.exceptions import OrderTooLargeError, EmptyOrderError


def make_mock_order_model():
    order = MagicMock()
    order.id = 1
    order.status = "pending"
    order.shipping_fee = Decimal("9.90")
    order.shipping_address_snapshot = {"city": "Paris"}
    order.created_at.isoformat.return_value = "2025-01-01T00:00:00"
    line = MagicMock()
    line.id = 1
    line.product_id = 1
    line.product_name_snapshot = "Stop Sign"
    line.quantity = 2
    line.unit_price = Decimal("50.00")
    line.total = Decimal("100.00")
    order.lines.all.return_value = [line]
    return order


@pytest.mark.django_db
class TestCreateOrderView:
    def test_api_returns_201_when_order_is_valid(self, client):
        # Arrange
        mock_order = make_mock_order_model()
        with patch("orders.api.views.OrderService") as MockService, \
             patch("orders.api.views.OrderModel.objects") as mock_manager:
            MockService.return_value.create_order.return_value = MagicMock(id=1)
            mock_manager.prefetch_related.return_value.get.return_value = mock_order

            # Act
            response = client.post(
                "/api/orders/",
                data={
                    "items": [{"product_id": 1, "quantity": 2}],
                    "shipping_address": {"city": "Paris"},
                    "guest_email": "guest@example.com",
                },
                content_type="application/json",
            )

        # Assert
        assert response.status_code == 201

    def test_api_returns_422_when_order_exceeds_max_quantity(self, client):
        # Arrange
        with patch("orders.api.views.OrderService") as MockService:
            MockService.return_value.create_order.side_effect = OrderTooLargeError(
                quantity=60, max_quantity=50
            )

            # Act
            response = client.post(
                "/api/orders/",
                data={
                    "items": [{"product_id": 1, "quantity": 60}],
                    "shipping_address": {},
                    "guest_email": "guest@example.com",
                },
                content_type="application/json",
            )

        # Assert
        assert response.status_code == 422
        assert response.json()["code"] == "order_too_large"

    def test_api_returns_400_when_items_list_is_empty(self, client):
        # Act
        response = client.post(
            "/api/orders/",
            data={"items": [], "shipping_address": {}, "guest_email": "g@example.com"},
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 400

    def test_api_returns_400_when_guest_email_missing_for_unauthenticated(self, client):
        # Act
        response = client.post(
            "/api/orders/",
            data={"items": [{"product_id": 1, "quantity": 1}], "shipping_address": {}},
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 400
        assert "guest_email" in response.json()

    def test_api_uses_customer_id_when_authenticated(self, authenticated_client, test_user):
        # Arrange
        mock_order = make_mock_order_model()
        with patch("orders.api.views.OrderService") as MockService, \
             patch("orders.api.views.OrderModel.objects") as mock_manager:
            mock_service = MockService.return_value
            mock_service.create_order.return_value = MagicMock(id=1)
            mock_manager.prefetch_related.return_value.get.return_value = mock_order

            # Act
            authenticated_client.post(
                "/api/orders/",
                data={
                    "items": [{"product_id": 1, "quantity": 1}],
                    "shipping_address": {},
                },
                content_type="application/json",
            )

        # Assert
        call_kwargs = mock_service.create_order.call_args[1]
        assert call_kwargs["customer_id"] == test_user.customer.id
