from django.db import transaction
from ..domain.entities import Order, OrderLine, OrderStatus
from ..models import OrderModel, OrderLineModel


class OrderRepository:
    def save(self, order: Order) -> Order:
        with transaction.atomic():
            order_model = OrderModel.objects.create(
                customer_id=order.customer_id,
                guest_email=order.guest_email,
                status=order.status.value,
                shipping_fee=order.shipping_fee,
                shipping_address_snapshot=order.shipping_address,
                stripe_session_id=order.stripe_session_id,
            )
            OrderLineModel.objects.bulk_create([
                OrderLineModel(
                    order=order_model,
                    product_id=line.product_id,
                    product_name_snapshot=line.product_name,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
                for line in order.lines
            ])
        order.id = order_model.id
        return order

    def get_by_id(self, order_id: int) -> Order:
        model = OrderModel.objects.prefetch_related("lines").get(id=order_id)
        return self._to_entity(model)

    def list_for_customer(self, customer_id: int) -> list[Order]:
        qs = (
            OrderModel.objects
            .filter(customer_id=customer_id)
            .prefetch_related("lines")
            .order_by("-created_at")
        )
        return [self._to_entity(m) for m in qs]

    def update_status(self, order_id: int, status: OrderStatus) -> None:
        OrderModel.objects.filter(id=order_id).update(status=status.value)

    def update_stripe_session(self, order_id: int, session_id: str) -> None:
        OrderModel.objects.filter(id=order_id).update(stripe_session_id=session_id)

    def get_by_stripe_session(self, session_id: str) -> Order:
        model = OrderModel.objects.prefetch_related("lines").get(stripe_session_id=session_id)
        return self._to_entity(model)

    def _to_entity(self, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            customer_id=model.customer_id,
            guest_email=model.guest_email,
            status=OrderStatus(model.status),
            shipping_fee=model.shipping_fee,
            shipping_address=model.shipping_address_snapshot,
            stripe_session_id=model.stripe_session_id,
            lines=[
                OrderLine(
                    product_id=line.product_id,
                    product_name=line.product_name_snapshot,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
                for line in model.lines.all()
            ],
        )
