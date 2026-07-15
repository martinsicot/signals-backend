from celery import shared_task


@shared_task
def send_order_confirmation(order_id: int) -> None:
    from .emails import send_order_confirmation as _send
    _send(order_id)


@shared_task
def send_payment_confirmation(order_id: int) -> None:
    from .emails import send_payment_confirmation as _send
    _send(order_id)
