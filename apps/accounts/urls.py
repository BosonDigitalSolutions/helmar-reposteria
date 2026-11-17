from django.urls import path

from .views import StaffLoginView, StaffLogoutView

app_name = "accounts"

urlpatterns = [
    path("entrar/", StaffLoginView.as_view(), name="login"),
    path("salir/", StaffLogoutView.as_view(), name="logout"),
]
