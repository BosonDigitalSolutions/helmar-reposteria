from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("aviso-de-privacidad/", views.privacy, name="privacy"),
]
