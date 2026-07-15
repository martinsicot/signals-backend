import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import RequestFactory
from cart.cart import Cart


def make_request_with_session():
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {}
    return request


@pytest.fixture
def mock_product():
    p = MagicMock()
    p.id = 1
    p.name = "Stop Sign"
    p.slug = "stop-sign"
    p.price = Decimal("49.90")
    return p


class TestCartAdd:
    def test_add_product_increments_quantity(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)

        # Act
        cart.add(product_id=1, quantity=2)
        cart.add(product_id=1, quantity=3)

        # Assert
        assert cart.cart["1"]["quantity"] == 5

    def test_add_product_with_override_replaces_quantity(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)
        cart.add(product_id=1, quantity=5)

        # Act
        cart.add(product_id=1, quantity=2, override_quantity=True)

        # Assert
        assert cart.cart["1"]["quantity"] == 2

    def test_add_multiple_products(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)

        # Act
        cart.add(product_id=1, quantity=1)
        cart.add(product_id=2, quantity=3)

        # Assert
        assert len(cart) == 4


class TestCartRemove:
    def test_remove_existing_product(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)
        cart.add(product_id=1, quantity=2)

        # Act
        cart.remove(product_id=1)

        # Assert
        assert "1" not in cart.cart

    def test_remove_nonexistent_product_is_safe(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)

        # Act & Assert — no exception
        cart.remove(product_id=99)


class TestCartClear:
    def test_clear_empties_cart(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)
        cart.add(product_id=1, quantity=2)
        cart.add(product_id=2, quantity=1)

        # Act
        cart.clear()

        # Assert
        assert len(cart) == 0

    def test_clear_on_empty_cart_is_safe(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)

        # Act & Assert — no exception
        cart.clear()


class TestCartToOrderItems:
    def test_to_order_items_returns_correct_format(self):
        # Arrange
        request = make_request_with_session()
        cart = Cart(request)
        cart.add(product_id=1, quantity=2)
        cart.add(product_id=3, quantity=1)

        # Act
        items = cart.to_order_items()

        # Assert
        assert {"product_id": 1, "quantity": 2} in items
        assert {"product_id": 3, "quantity": 1} in items
