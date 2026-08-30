from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm, RegisterForm
from .models import Customer

User = get_user_model()


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, "accounts/login.html", {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/login.html", {"form": form})

        user = authenticate(request, email=form.cleaned_data["email"], password=form.cleaned_data["password"])
        if user is None:
            form.add_error(None, "Email ou mot de passe incorrect.")
            return render(request, "accounts/login.html", {"form": form})

        login(request, user)
        next_url = request.GET.get("next") or "home"
        return redirect(next_url)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("home")


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, "accounts/register.html", {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/register.html", {"form": form})

        data = form.cleaned_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        Customer.objects.create(user=user, phone=data.get("phone", ""))
        login(request, user)
        messages.success(request, "Bienvenue ! Votre compte a été créé.")
        return redirect("home")


@method_decorator(login_required(login_url="/connexion/"), name="dispatch")
class ProfileView(View):
    def get(self, request):
        return render(request, "accounts/profile.html")
