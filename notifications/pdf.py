from io import BytesIO
from django.template.loader import render_to_string
import weasyprint


def generate_invoice_pdf(order) -> bytes:
    html = render_to_string("notifications/invoice.html", {"order": order})
    pdf = weasyprint.HTML(string=html, base_url="/").write_pdf()
    return pdf
