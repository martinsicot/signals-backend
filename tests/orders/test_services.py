from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from orders.domain.entities import OrderStatus
from orders.domain.exceptions import EmptyOrderError, OrderTooLargeError
from orders.services.order_service import OrderService


@pytest.fixture
def mock_product():
    product = MagicMock()
    product.name = "Stop Sign"
    return product


@pytest.fixture
def order_service(mock_product):
    service = OrderService.__new__(OrderService)
    service.order_repo = MagicMock()
    service.product_repo = MagicMock()
    service.product_repo.get_by_id.return_value = mock_product
    service.product_repo.get_price.return_value = Decimal("50.00")
    service.order_repo.save.return_value = MagicMock(id=1)
    return service


class TestCreateOrder:
    def test_create_order_sets_correct_status(self, order_service):
        # Act
        order_service.create_order(
            cart_items=[{"product_id": 1, "quantity": 1}],
            shipping_address={"city": "Paris"},
            customer_id=1,
        )

        # Assert
        saved_order = order_service.order_repo.save.call_args[0][0]
        assert saved_order.status == OrderStatus.PENDING

    def test_create_order_computes_correct_subtotal(self, order_service):
        # Arrange — product price is 50.00, quantity 2 → subtotal 100.00

        # Act
        order_service.create_order(
            cart_items=[{"product_id": 1, "quantity": 2}],
            shipping_address={},
            customer_id=1,
        )

        # Assert
        saved_order = order_service.order_repo.save.call_args[0][0]
        assert saved_order.subtotal == Decimal("100.00")

    def test_create_order_applies_shipping_fee_below_threshold(self, order_service):
        # Arrange — subtotal 50.00 < threshold 200.00 → fee applies
        with patch("orders.services.order_service.settings") as mock_settings:
            mock_settings.SHIPPING_FREE_THRESHOLD = Decimal("200.00")
            mock_settings.SHIPPING_FEE = Decimal("9.90")
            mock_settings.MAX_QUANTITY_INDIVIDUAL = 50

            # Act
            order_service.create_order(
                cart_items=[{"product_id": 1, "quantity": 1}],
                shipping_address={},
                customer_id=1,
            )

        # Assert
        saved_order = order_service.order_repo.save.call_args[0][0]
        assert saved_order.shipping_fee == Decimal("9.90")

    def test_create_order_raises_when_cart_is_empty(self, order_service):
        # Act & Assert
        with pytest.raises(EmptyOrderError):
            order_service.create_order(
                cart_items=[],
                shipping_address={},
                customer_id=1,
            )

    def test_create_order_sets_guest_email_when_no_customer(self, order_service):
        # Act
        order_service.create_order(
            cart_items=[{"product_id": 1, "quantity": 1}],
            shipping_address={},
            guest_email="guest@example.com",
        )

        # Assert
        saved_order = order_service.order_repo.save.call_args[0][0]
        assert saved_order.guest_email == "guest@example.com"
        assert saved_order.customer_id is None

    def test_create_order_snapshots_product_name(self, order_service):
        # Act
        order_service.create_order(
            cart_items=[{"product_id": 1, "quantity": 1}],
            shipping_address={},
            customer_id=1,
        )

        # Assert
        saved_order = order_service.order_repo.save.call_args[0][0]
        assert saved_order.lines[0].product_name == "Stop Sign"
