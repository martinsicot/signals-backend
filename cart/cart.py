from decimal import Decimal
from catalog.repositories.product_repository import ProductRepository


class Cart:
    """
    Session-based cart — works for both authenticated and guest users.
    Stored as: session["cart_v2"] = {"<variant_id>": {"quantity": int}}
    """

    SESSION_KEY = "cart_v2"

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def add(self, variant_id: int, quantity: int = 1, override_quantity: bool = False) -> None:
        key = str(variant_id)
        if key not in self.cart:
            self.cart[key] = {"quantity": 0}
        if override_quantity:
            self.cart[key]["quantity"] = quantity
        else:
            self.cart[key]["quantity"] += quantity
        self._save()

    def remove(self, variant_id: int) -> None:
        key = str(variant_id)
        if key in self.cart:
            del self.cart[key]
            self._save()

    def clear(self) -> None:
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
            self._save()

    def __len__(self) -> int:
        return sum(item["quantity"] for item in self.cart.values())

    def __iter__(self):
        if not self.cart:
            return
        variant_ids = [int(k) for k in self.cart]
        repo = ProductRepository()
        variants = {v.id: v for v in repo.list_active_variants_by_ids(variant_ids)}
        for vid_str, item in self.cart.items():
            variant = variants.get(int(vid_str))
            if variant:
                yield {
                    "variant_id": variant.id,
                    "sku": variant.sku,
                    "product_name": variant.product.name,
                    "product_slug": variant.product.slug,
                    "quantity": item["quantity"],
                    "unit_price": str(variant.price),
                    "total_price": str(variant.price * item["quantity"]),
                }

    def get_subtotal(self) -> Decimal:
        if not self.cart:
            return Decimal("0")
        repo = ProductRepository()
        total = Decimal("0")
        for vid_str, item in self.cart.items():
            try:
                price = repo.get_variant_price(int(vid_str))
                total += price * item["quantity"]
            except Exception:
                pass
        return total

    def to_order_items(self) -> list[dict]:
        return [
            {"variant_id": int(k), "quantity": v["quantity"]}
            for k, v in self.cart.items()
        ]

    def _save(self) -> None:
        self.session.modified = True
