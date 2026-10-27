from django.template.loader import render_to_string
import weasyprint


def generate_payment_receipt_pdf(order, ctx: dict) -> bytes:
    html = render_to_string("notifications/payment_receipt.html", ctx)
    return weasyprint.HTML(string=html, base_url="/").write_pdf()
