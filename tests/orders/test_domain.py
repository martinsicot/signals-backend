from decimal import Decimal
import pytest
from orders.domain.entities import Order, OrderLine, OrderStatus
from orders.domain.rules import compute_shipping_fee, validate_order
from orders.domain.exceptions import EmptyOrderError, OrderTooLargeError


def make_order(lines=None, shipping_fee=Decimal("9.90")):
    return Order(
        customer_id=1,
        guest_email="",
        lines=lines or [],
        status=OrderStatus.PENDING,
        shipping_fee=shipping_fee,
        shipping_address={},
    )


def make_line(product_id=1, quantity=1, unit_price=Decimal("50.00")):
    return OrderLine(
        product_id=product_id,
        product_name="Stop Sign",
        quantity=quantity,
        unit_price=unit_price,
    )


class TestOrderLineTotal:
    def test_total_is_quantity_times_unit_price(self):
        # Arrange
        line = make_line(quantity=3, unit_price=Decimal("25.00"))

        # Act
        total = line.total

        # Assert
        assert total == Decimal("75.00")


class TestOrderSubtotal:
    def test_subtotal_sums_all_lines(self):
        # Arrange
        order = make_order(lines=[
            make_line(quantity=2, unit_price=Decimal("50.00")),
            make_line(quantity=1, unit_price=Decimal("30.00")),
        ])

        # Act & Assert
        assert order.subtotal == Decimal("130.00")

    def test_total_includes_shipping_fee(self):
        # Arrange
        order = make_order(
            lines=[make_line(quantity=1, unit_price=Decimal("100.00"))],
            shipping_fee=Decimal("9.90"),
        )

        # Act & Assert
        assert order.total == Decimal("109.90")

    def test_total_with_zero_shipping_fee(self):
        # Arrange
        order = make_order(
            lines=[make_line(quantity=1, unit_price=Decimal("250.00"))],
            shipping_fee=Decimal("0"),
        )

        # Act & Assert
        assert order.total == Decimal("250.00")


class TestShippingFeeComputation:
    def test_shipping_fee_is_zero_when_subtotal_above_threshold(self):
        # Arrange
        subtotal = Decimal("250.00")

        # Act
        fee = compute_shipping_fee(subtotal, free_threshold=Decimal("200.00"), fee=Decimal("9.90"))

        # Assert
        assert fee == Decimal("0")

    def test_shipping_fee_is_zero_when_subtotal_equals_threshold(self):
        # Arrange
        subtotal = Decimal("200.00")

        # Act
        fee = compute_shipping_fee(subtotal, free_threshold=Decimal("200.00"), fee=Decimal("9.90"))

        # Assert
        assert fee == Decimal("0")

    def test_shipping_fee_applied_when_subtotal_below_threshold(self):
        # Arrange
        subtotal = Decimal("150.00")

        # Act
        fee = compute_shipping_fee(subtotal, free_threshold=Decimal("200.00"), fee=Decimal("9.90"))

        # Assert
        assert fee == Decimal("9.90")

    def test_shipping_fee_applied_just_below_threshold(self):
        # Arrange
        subtotal = Decimal("199.99")

        # Act
        fee = compute_shipping_fee(subtotal, free_threshold=Decimal("200.00"), fee=Decimal("9.90"))

        # Assert
        assert fee == Decimal("9.90")


class TestOrderValidation:
    def test_validate_order_raises_error_when_cart_is_empty(self):
        # Arrange
        order = make_order(lines=[])

        # Act & Assert
        with pytest.raises(EmptyOrderError):
            validate_order(order, max_quantity=50)

    def test_validate_order_raises_error_when_quantity_exceeds_max(self):
        # Arrange
        order = make_order(lines=[make_line(quantity=51)])

        # Act & Assert
        with pytest.raises(OrderTooLargeError) as exc_info:
            validate_order(order, max_quantity=50)
        assert exc_info.value.quantity == 51
        assert exc_info.value.max_quantity == 50

    def test_validate_order_raises_error_when_multi_line_total_exceeds_max(self):
        # Arrange
        order = make_order(lines=[
            make_line(product_id=1, quantity=30),
            make_line(product_id=2, quantity=25),
        ])

        # Act & Assert
        with pytest.raises(OrderTooLargeError) as exc_info:
            validate_order(order, max_quantity=50)
        assert exc_info.value.quantity == 55

    def test_validate_order_passes_when_quantity_at_max(self):
        # Arrange
        order = make_order(lines=[make_line(quantity=50)])

        # Act & Assert — no exception raised
        validate_order(order, max_quantity=50)

    def test_validate_order_passes_for_valid_multi_line_order(self):
        # Arrange
        order = make_order(lines=[
            make_line(quantity=2),
            make_line(product_id=2, quantity=3),
        ])

        # Act & Assert — no exception raised
        validate_order(order, max_quantity=50)
