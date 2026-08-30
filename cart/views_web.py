from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.conf import settings
from .cart import Cart
from orders.domain.rules import compute_shipping_fee


class CartView(View):
    def get(self, request):
        cart = Cart(request)
        subtotal = cart.get_subtotal()
        shipping_fee = compute_shipping_fee(
            subtotal,
            free_threshold=settings.SHIPPING_FREE_THRESHOLD,
            fee=settings.SHIPPING_FEE,
        )
        return render(request, "cart/cart.html", {
            "items": list(cart),
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "total": subtotal + shipping_fee,
            "free_threshold": settings.SHIPPING_FREE_THRESHOLD,
        })


class CartAddView(View):
    def post(self, request):
        try:
            product_id = int(request.POST.get("product_id", 0))
            quantity = int(request.POST.get("quantity", 1))
            assert product_id > 0 and quantity >= 1
        except (ValueError, AssertionError):
            return HttpResponse(status=400)

        cart = Cart(request)
        cart.add(product_id=product_id, quantity=quantity)

        # HTMX — return just the updated count badge
        if request.headers.get("HX-Request"):
            return HttpResponse(
                f'<span id="cart-count" class="bg-blue-700 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center">{len(cart)}</span>',
                content_type="text/html",
            )
        return redirect("cart")


class CartUpdateView(View):
    def post(self, request, product_id):
        try:
            quantity = int(request.POST.get("quantity", 0))
        except (ValueError, TypeError):
            return HttpResponse(status=400)

        cart = Cart(request)
        if quantity <= 0:
            cart.remove(product_id)
        else:
            cart.add(product_id=product_id, quantity=quantity, override_quantity=True)
        return redirect("cart")


class CartRemoveView(View):
    def post(self, request, product_id):
        Cart(request).remove(product_id)
        return redirect("cart")
