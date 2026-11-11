from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/login/", views.api_login),
    path("api/logout/", views.api_logout),
    path("healthz", views.health),
]
