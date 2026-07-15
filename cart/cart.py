from decimal import Decimal
from catalog.repositories.product_repository import ProductRepository


class Cart:
    """
    Session-based cart — works for both authenticated and guest users.
    Stored as: session["cart"] = {"<product_id>": {"quantity": int}}
    """

    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def add(self, product_id: int, quantity: int = 1, override_quantity: bool = False) -> None:
        key = str(product_id)
        if key not in self.cart:
            self.cart[key] = {"quantity": 0}
        if override_quantity:
            self.cart[key]["quantity"] = quantity
        else:
            self.cart[key]["quantity"] += quantity
        self._save()

    def remove(self, product_id: int) -> None:
        key = str(product_id)
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
        product_ids = [int(k) for k in self.cart]
        repo = ProductRepository()
        products = {p.id: p for p in repo.list_active() if p.id in product_ids}
        for product_id_str, item in self.cart.items():
            product = products.get(int(product_id_str))
            if product:
                yield {
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_slug": product.slug,
                    "quantity": item["quantity"],
                    "unit_price": str(product.price),
                    "total_price": str(product.price * item["quantity"]),
                }

    def get_subtotal(self) -> Decimal:
        if not self.cart:
            return Decimal("0")
        repo = ProductRepository()
        total = Decimal("0")
        for product_id_str, item in self.cart.items():
            try:
                price = repo.get_price(int(product_id_str))
                total += price * item["quantity"]
            except Exception:
                pass
        return total

    def to_order_items(self) -> list[dict]:
        return [
            {"product_id": int(k), "quantity": v["quantity"]}
            for k, v in self.cart.items()
        ]

    def _save(self) -> None:
        self.session.modified = True
