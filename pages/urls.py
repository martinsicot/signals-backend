from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("cgv/", views.CGVView.as_view(), name="cgv"),
    path("mentions-legales/", views.MentionsLegalesView.as_view(), name="mentions-legales"),
]
