from decimal import Decimal
from django.conf import settings
from ..domain.entities import Order, OrderLine, OrderStatus
from ..domain.rules import compute_shipping_fee, validate_order
from ..repositories.order_repository import OrderRepository
from catalog.repositories.product_repository import ProductRepository


class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()

    def create_order(
        self,
        cart_items: list[dict],
        shipping_address: dict,
        customer_id: int | None = None,
        guest_email: str = "",
    ) -> Order:
        lines = [
            OrderLine(
                product_id=item["product_id"],
                product_name=self.product_repo.get_by_id(item["product_id"]).name,
                quantity=int(item["quantity"]),
                unit_price=self.product_repo.get_price(item["product_id"]),
            )
            for item in cart_items
        ]

        subtotal = sum((line.total for line in lines), Decimal("0"))
        shipping_fee = compute_shipping_fee(
            subtotal,
            free_threshold=settings.SHIPPING_FREE_THRESHOLD,
            fee=settings.SHIPPING_FEE,
        )

        order = Order(
            customer_id=customer_id,
            guest_email=guest_email,
            lines=lines,
            status=OrderStatus.PENDING,
            shipping_fee=shipping_fee,
            shipping_address=shipping_address,
        )

        validate_order(order, max_quantity=settings.MAX_QUANTITY_INDIVIDUAL)

        order = self.order_repo.save(order)

        from notifications.tasks import send_order_confirmation
        send_order_confirmation.delay(order.id)

        return order

    def mark_as_paid(self, order_id: int) -> None:
        self.order_repo.update_status(order_id, OrderStatus.PAID)

    def get_order(self, order_id: int) -> Order:
        return self.order_repo.get_by_id(order_id)

    def list_customer_orders(self, customer_id: int) -> list[Order]:
        return self.order_repo.list_for_customer(customer_id)
