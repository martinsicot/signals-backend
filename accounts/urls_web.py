from django.urls import path
from .views_web import LoginView, LogoutView, RegisterView, ProfileView

urlpatterns = [
    path("connexion/", LoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("inscription/", RegisterView.as_view(), name="register"),
    path("mon-compte/", ProfileView.as_view(), name="profile"),
]
