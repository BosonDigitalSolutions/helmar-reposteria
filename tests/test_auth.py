import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.accounts.models import User
from tests.factories import UserFactory


def test_custom_user_model():
    assert settings.AUTH_USER_MODEL == "accounts.User"


@pytest.mark.django_db
def test_role_groups_exist():
    names = set(Group.objects.values_list("name", flat=True))
    assert {"Administrador", "Ventas", "Producción"} <= names
    assert Group.objects.get(name="Administrador").permissions.exists()


@pytest.mark.django_db
def test_saving_a_user_assigns_the_role_group():
    user = UserFactory(role=User.Role.PRODUCCION)
    assert list(user.groups.values_list("name", flat=True)) == ["Producción"]
    assert user.is_staff is False

    user.role = User.Role.VENTAS
    user.save()
    assert list(user.groups.values_list("name", flat=True)) == ["Ventas"]


@pytest.mark.django_db
def test_administrator_is_staff():
    user = UserFactory(role=User.Role.ADMINISTRADOR)
    assert user.is_staff is True
    assert user.groups.filter(name="Administrador").exists()


@pytest.mark.django_db
def test_invalid_role_is_rejected():
    user = UserFactory()
    user.role = "invitado"
    with pytest.raises(ValueError):
        user.save()


@pytest.mark.django_db
def test_anonymous_dashboard_redirects_to_login(client):
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_login_redirects_to_dashboard(client):
    user = UserFactory(role=User.Role.VENTAS, password="clave-segura-123")
    response = client.post(
        reverse("accounts:login"),
        {"username": user.username, "password": "clave-segura-123"},
    )
    assert response.status_code == 302
    assert response.url == reverse("dashboard:home")

    home = client.get(reverse("dashboard:home"))
    body = home.content.decode()
    assert home.status_code == 200
    assert "Cotizaciones abiertas" in body
    assert "Cerrar sesión" in body
    assert "Ventas" in body


@pytest.mark.django_db
def test_user_without_role_group_gets_forbidden(client):
    user = UserFactory(role=User.Role.VENTAS)
    user.groups.clear()
    client.force_login(user)
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_open_dashboard_without_role_group(client):
    user = UserFactory(role=User.Role.VENTAS)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    user.groups.clear()
    client.force_login(user)
    assert client.get(reverse("dashboard:home")).status_code == 200


@pytest.mark.django_db
def test_logout_is_post_only_and_returns_home(client):
    user = UserFactory()
    client.force_login(user)
    assert client.get(reverse("accounts:logout")).status_code == 405
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302
    assert response.url == reverse("core:landing")


@pytest.mark.django_db
def test_admin_login_is_available(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
