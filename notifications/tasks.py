from celery import shared_task


@shared_task
def send_order_confirmation(order_id: int) -> None:
    from .emails import send_order_confirmation as _send
    _send(order_id)


@shared_task
def send_payment_confirmation(order_id: int) -> None:
    from .emails import send_payment_confirmation as _send
    _send(order_id)


@shared_task
def send_order_in_production(order_id: int) -> None:
    from .emails import send_order_in_production as _send
    _send(order_id)


@shared_task
def send_order_shipped(order_id: int, tracking_number: str | None = None) -> None:
    from .emails import send_order_shipped as _send
    _send(order_id, tracking_number)


@shared_task
def send_order_delivered(order_id: int) -> None:
    from .emails import send_order_delivered as _send
    _send(order_id)
