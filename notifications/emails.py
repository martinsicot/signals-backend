from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _load_order(order_id: int):
    from orders.models import OrderModel
    return OrderModel.objects.prefetch_related("lines").get(id=order_id)


def _build_context(order) -> dict:
    vat = settings.VAT_RATE
    lines = []
    subtotal_ht = Decimal("0")

    for line in order.lines.all():
        ht = line.unit_price * line.quantity
        lines.append({
            "name": line.product_name_snapshot,
            "quantity": line.quantity,
            "unit_price_ht": line.unit_price,
            "unit_price_ttc": round(line.unit_price * (1 + vat), 2),
            "total_ht": ht,
            "total_ttc": round(ht * (1 + vat), 2),
        })
        subtotal_ht += ht

    shipping_ht = order.shipping_fee
    total_ht = subtotal_ht + shipping_ht
    tva_amount = round(total_ht * vat, 2)
    total_ttc = round(total_ht * (1 + vat), 2)

    return {
        "order": order,
        "lines": lines,
        "subtotal_ht": subtotal_ht,
        "shipping_ht": shipping_ht,
        "shipping_ttc": round(shipping_ht * (1 + vat), 2),
        "tva_amount": tva_amount,
        "total_ht": total_ht,
        "total_ttc": total_ttc,
        "vat_rate": int(vat * 100),
    }


def send_order_confirmation(order_id: int) -> None:
    order = _load_order(order_id)
    ctx = _build_context(order)
    subject = f"Commande n° {order.id} reçue — Le Panneau"
    body = render_to_string("notifications/order_confirmation.txt", ctx)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.contact_email])


def send_payment_confirmation(order_id: int) -> None:
    from django.core.mail import EmailMessage
    from .pdf import generate_payment_receipt_pdf

    order = _load_order(order_id)
    ctx = _build_context(order)

    subject = f"Paiement confirmé — Commande n° {order.id} | Le Panneau"
    body = render_to_string("notifications/payment_confirmation.txt", ctx)

    pdf_bytes = generate_payment_receipt_pdf(order, ctx)
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [order.contact_email])
    email.attach(f"preuve_paiement_{order.id}.pdf", pdf_bytes, "application/pdf")
    email.send()

    admin_body = render_to_string("notifications/new_order_admin.txt", ctx)
    send_mail(
        f"[NOUVELLE COMMANDE] n° {order.id} — {order.contact_email}",
        admin_body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
    )


def send_order_in_production(order_id: int) -> None:
    order = _load_order(order_id)
    ctx = _build_context(order)
    subject = f"Commande n° {order.id} en cours de fabrication — Le Panneau"
    body = render_to_string("notifications/order_in_production.txt", ctx)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.contact_email])


def send_order_shipped(order_id: int, tracking_number: str | None = None) -> None:
    order = _load_order(order_id)
    ctx = _build_context(order)
    ctx["tracking_number"] = tracking_number
    subject = f"Commande n° {order.id} expédiée — Le Panneau"
    body = render_to_string("notifications/order_shipped.txt", ctx)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.contact_email])


def send_order_delivered(order_id: int) -> None:
    order = _load_order(order_id)
    ctx = _build_context(order)
    subject = f"Commande n° {order.id} livrée — Le Panneau"
    body = render_to_string("notifications/order_delivered.txt", ctx)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.contact_email])
