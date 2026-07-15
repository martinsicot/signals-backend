from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_order_confirmation(order_id: int) -> None:
    from orders.models import OrderModel
    order = OrderModel.objects.prefetch_related("lines").get(id=order_id)
    recipient = order.contact_email

    subject = f"Order #{order.id} confirmed — Signals"
    body = render_to_string("notifications/order_confirmation.txt", {"order": order})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])


def send_payment_confirmation(order_id: int) -> None:
    from orders.models import OrderModel
    from django.core.mail import EmailMessage
    from .pdf import generate_invoice_pdf

    order = OrderModel.objects.prefetch_related("lines").get(id=order_id)
    recipient = order.contact_email

    subject = f"Payment received for order #{order.id} — Signals"
    body = render_to_string("notifications/payment_confirmation.txt", {"order": order})

    pdf_bytes = generate_invoice_pdf(order)
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])
    email.attach(f"invoice_{order.id}.pdf", pdf_bytes, "application/pdf")
    email.send()

    # Notify admin / associate
    admin_body = render_to_string("notifications/new_order_admin.txt", {"order": order})
    send_mail(
        f"[NEW ORDER] #{order.id} — {order.contact_email}",
        admin_body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
    )
