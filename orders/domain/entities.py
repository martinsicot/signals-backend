from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    IN_PRODUCTION = "in_production"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderLine:
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    customer_id: int | None
    guest_email: str
    lines: list[OrderLine]
    status: OrderStatus
    shipping_fee: Decimal
    shipping_address: dict
    id: int | None = None
    stripe_session_id: str = ""

    @property
    def subtotal(self) -> Decimal:
        return sum((line.total for line in self.lines), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.shipping_fee
