from decimal import Decimal
from .entities import Order
from .exceptions import EmptyOrderError, OrderTooLargeError


def compute_shipping_fee(
    subtotal: Decimal,
    *,
    free_threshold: Decimal,
    fee: Decimal,
) -> Decimal:
    if subtotal >= free_threshold:
        return Decimal("0")
    return fee


def validate_order(order: Order, *, max_quantity: int) -> None:
    if not order.lines:
        raise EmptyOrderError()

    total_qty = sum(line.quantity for line in order.lines)
    if total_qty > max_quantity:
        raise OrderTooLargeError(quantity=total_qty, max_quantity=max_quantity)
