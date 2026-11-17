from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

DEMO_PRODUCTS = (
    "Pastel de celebración",
    "Galletas decoradas",
    "Cupcakes de fiesta",
    "Pastel de chocolate",
    "Caja de galletas",
    "Pastel floral",
)


@pytest.mark.django_db
def test_landing_keeps_brand_and_login(client):
    response = client.get(reverse("core:landing"))
    html = response.content.decode()
    header = html[html.index("<header") : html.index("</header>")]
    body = html[html.index("</header>") :]

    assert response.status_code == 200
    assert 'lang="es"' in html
    assert "HelyMar Repostería" in html
    assert "static/img/helymar-logo" in html
    assert "Logotipo de HelyMar Repostería" in html
    assert 'id="loginModal"' in header
    assert "data-open-login" in header
    assert reverse("accounts:login") in header
    assert "data-whatsapp" not in header
    assert "data-open-catalog" not in header
    assert "Explorar catálogo" in body
    assert "Cotizar" in body
    assert 'id="catalogModal"' in html
    assert 'aria-labelledby="catalogTitle"' in html
    assert 'aria-label="Cerrar catálogo"' in html
    assert 'aria-label="Buscar productos"' in html
    assert 'aria-label="Abrir menú"' in html
    assert "<main>" in html
    assert 'id="catalog-data" type="application/json">[]</script>' in html
    assert "El catálogo se publicará aquí cuando haya productos reales." in html
    for name in DEMO_PRODUCTS:
        assert name not in html


@pytest.mark.django_db
def test_privacy_notice_is_pending(client):
    response = client.get(reverse("core:privacy"))
    html = response.content.decode()
    assert response.status_code == 200
    assert "pendiente" in html.lower()


@pytest.mark.django_db
def test_there_is_no_public_signup(client):
    for path in ("/cuenta/registro/", "/registro/", "/accounts/signup/"):
        assert client.get(path).status_code == 404


def test_local_database_is_sqlite():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_landing_script_supports_keyboard_and_focus():
    script = Path(settings.BASE_DIR, "static", "js", "landing.js").read_text(encoding="utf-8")
    css = Path(settings.BASE_DIR, "static", "css", "landing.css").read_text(encoding="utf-8")
    assert "ArrowDown" in script
    assert "a[data-whatsapp], button[data-whatsapp]" in script
    assert "lastFocus" in script
    assert "prefers-reduced-motion" in script
    assert "scroll-snap-type" in css
    assert "prefers-reduced-motion" in css


@pytest.mark.django_db
def test_local_whatsapp_test_number_reaches_the_page(client):
    response = client.get(reverse("core:landing"))
    assert 'data-whatsapp="5638773661"' in response.content.decode()
