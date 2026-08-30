from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django import forms
from cart.cart import Cart
from .services.order_service import OrderService
from .services.payment_service import PaymentService
from .domain.exceptions import EmptyOrderError, OrderTooLargeError, ProductNotAvailableError
from .models import OrderModel


class ShippingForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Prénom", "autocomplete": "given-name"})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Nom", "autocomplete": "family-name"})
    )
    company = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Société (optionnel)"})
    )
    line1 = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Adresse", "autocomplete": "address-line1"})
    )
    line2 = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Complément d'adresse", "autocomplete": "address-line2"})
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Code postal", "autocomplete": "postal-code"})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "Ville", "autocomplete": "address-level2"})
    )
    guest_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500", "placeholder": "votre@email.fr", "autocomplete": "email"})
    )


class CheckoutView(View):
    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return redirect("cart")
        form = ShippingForm()
        if request.user.is_authenticated and hasattr(request.user, "customer"):
            default_addr = request.user.customer.addresses.filter(is_default=True).first()
            if default_addr:
                form = ShippingForm(initial={
                    "first_name": default_addr.first_name,
                    "last_name": default_addr.last_name,
                    "company": default_addr.company,
                    "line1": default_addr.line1,
                    "line2": default_addr.line2,
                    "postal_code": default_addr.postal_code,
                    "city": default_addr.city,
                })
        return render(request, "orders/checkout.html", {"form": form, "cart": cart})

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return redirect("cart")

        form = ShippingForm(request.POST)

        # Guest checkout requires email
        if not request.user.is_authenticated:
            form.fields["guest_email"].required = True

        if not form.is_valid():
            return render(request, "orders/checkout.html", {"form": form, "cart": cart})

        data = form.cleaned_data
        shipping_address = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "company": data.get("company", ""),
            "line1": data["line1"],
            "line2": data.get("line2", ""),
            "postal_code": data["postal_code"],
            "city": data["city"],
            "country": "FR",
        }

        customer_id = None
        guest_email = ""
        if request.user.is_authenticated and hasattr(request.user, "customer"):
            customer_id = request.user.customer.id
        else:
            guest_email = data.get("guest_email", "")

        service = OrderService()
        try:
            order = service.create_order(
                cart_items=cart.to_order_items(),
                shipping_address=shipping_address,
                customer_id=customer_id,
                guest_email=guest_email,
            )
        except EmptyOrderError:
            messages.error(request, "Votre panier est vide.")
            return redirect("cart")
        except OrderTooLargeError as e:
            messages.error(request, str(e))
            return render(request, "orders/checkout.html", {"form": form, "cart": cart})
        except ProductNotAvailableError as e:
            messages.error(request, str(e))
            return render(request, "orders/checkout.html", {"form": form, "cart": cart})

        payment = PaymentService()
        try:
            checkout_url = payment.create_checkout_session(
                order_id=order.id,
                success_url=request.build_absolute_uri(f"/mes-commandes/{order.id}/confirmation/"),
                cancel_url=request.build_absolute_uri("/panier/"),
            )
        except Exception:
            messages.error(request, "Une erreur est survenue lors de la création du paiement. Veuillez réessayer.")
            return render(request, "orders/checkout.html", {"form": form, "cart": cart})

        cart.clear()
        return redirect(checkout_url)


class OrderConfirmationView(View):
    def get(self, request, order_id):
        if request.user.is_authenticated and hasattr(request.user, "customer"):
            order = get_object_or_404(OrderModel.objects.prefetch_related("lines"), id=order_id, customer=request.user.customer)
        else:
            # Guest — allow access if order_id in session
            confirmed_ids = request.session.get("confirmed_orders", [])
            if order_id not in confirmed_ids:
                return redirect("home")
            order = get_object_or_404(OrderModel.objects.prefetch_related("lines"), id=order_id)
        return render(request, "orders/confirmation.html", {"order": order})


@method_decorator(login_required(login_url="/connexion/"), name="dispatch")
class OrderListView(View):
    def get(self, request):
        orders = OrderModel.objects.filter(customer=request.user.customer).prefetch_related("lines").order_by("-created_at")
        return render(request, "orders/order_list.html", {"orders": orders})


@method_decorator(login_required(login_url="/connexion/"), name="dispatch")
class OrderDetailView(View):
    def get(self, request, order_id):
        order = get_object_or_404(OrderModel.objects.prefetch_related("lines"), id=order_id, customer=request.user.customer)
        return render(request, "orders/order_detail.html", {"order": order})
