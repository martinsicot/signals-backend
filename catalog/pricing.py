from decimal import Decimal
from django.conf import settings


def apply_markup(price: Decimal | None) -> Decimal | None:
    """Return price after applying PRICE_MARKUP coefficient."""
    if price is None:
        return None
    return price * settings.PRICE_MARKUP


def price_ttc(price_ht: Decimal | None) -> Decimal | None:
    """Return TTC amount after markup and VAT."""
    marked = apply_markup(price_ht)
    if marked is None:
        return None
    return round(marked * (Decimal("1") + settings.VAT_RATE), 2)
