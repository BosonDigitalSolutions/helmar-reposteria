import json
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from tests.factories import UserFactory


def png_file(name="foto.png"):
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (184, 47, 43)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def product_payload(**overrides):
    category = Category.objects.get(slug="cupcakes")
    payload = {
        "name": "Cupcake de prueba",
        "sku": "CUP-1",
        "category": category.pk,
        "description": "Cobertura a definir con el cliente.",
        "price_mode": Product.PriceMode.QUOTE,
        "base_price": "",
        "is_customizable": "on",
        "is_active": "on",
        "lead_time_days": 2,
        "display_order": 1,
        "presentations-TOTAL_FORMS": 1,
        "presentations-INITIAL_FORMS": 0,
        "presentations-MIN_NUM_FORMS": 0,
        "presentations-MAX_NUM_FORMS": 1000,
        "presentations-0-name": "Media docena",
        "presentations-0-display_order": 1,
        "presentations-0-id": "",
        "options-TOTAL_FORMS": 1,
        "options-INITIAL_FORMS": 0,
        "options-MIN_NUM_FORMS": 0,
        "options-MAX_NUM_FORMS": 1000,
        "options-0-name": "",
        "options-0-display_order": 0,
        "options-0-id": "",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_initial_categories_exist():
    names = set(Category.objects.values_list("name", flat=True))
    assert "Pasteles personalizados" in names
    assert "Galletas personalizadas" in names
    assert "Cupcakes" in names
    assert "Cajas de regalo" in names
    assert "Postres individuales" in names
    assert "Eventos especiales" in names


@pytest.mark.django_db
def test_admin_creates_product_and_public_catalog_hides_inactive(client):
    admin = UserFactory(role=User.Role.ADMINISTRADOR, password="clave-segura-123")
    client.force_login(admin)
    response = client.post(reverse("catalog:product_create"), product_payload(), follow=True)
    assert response.status_code == 200
    product = Product.objects.get(sku="CUP-1")
    assert product.presentations.filter(name="Media docena").exists()
    assert product.price_label == "Sujeto a cotización"

    landing = client.get(reverse("core:landing"))
    catalog = landing.content.decode()
    assert "Cupcake de prueba" in catalog

    product.is_active = False
    product.save(update_fields=["is_active"])
    hidden = client.get(reverse("core:landing")).content.decode()
    assert "Cupcake de prueba" not in hidden


@pytest.mark.django_db
def test_base_price_uses_decimal_and_rejects_quote_with_price(client):
    admin = UserFactory(role=User.Role.ADMINISTRADOR)
    client.force_login(admin)
    response = client.post(
        reverse("catalog:product_create"),
        product_payload(price_mode=Product.PriceMode.FROM_BASE, base_price="180.50", sku="CUP-2"),
    )
    assert response.status_code == 302
    product = Product.objects.get(sku="CUP-2")
    assert str(product.base_price) == "180.50"
    assert product.price_label == "Desde $180.50"

    rejected = client.post(
        reverse("catalog:product_create"),
        product_payload(price_mode=Product.PriceMode.QUOTE, base_price="10.00", sku="CUP-3"),
    )
    assert rejected.status_code == 200
    assert not Product.objects.filter(sku="CUP-3").exists()


@pytest.mark.django_db
def test_sales_can_view_but_not_create_products(client):
    sales = UserFactory(role=User.Role.VENTAS)
    client.force_login(sales)
    assert client.get(reverse("catalog:product_list")).status_code == 200
    assert client.get(reverse("catalog:product_create")).status_code == 403


@pytest.mark.django_db
def test_invalid_image_is_rejected(client):
    admin = UserFactory(role=User.Role.ADMINISTRADOR)
    client.force_login(admin)
    payload = product_payload(sku="CUP-4")
    payload["new_image"] = SimpleUploadedFile("nota.txt", b"no-es-imagen", content_type="text/plain")
    response = client.post(reverse("catalog:product_create"), payload)
    assert response.status_code == 200
    assert not Product.objects.filter(sku="CUP-4").exists()


@pytest.mark.django_db
def test_valid_image_is_stored(client):
    admin = UserFactory(role=User.Role.ADMINISTRADOR)
    client.force_login(admin)
    payload = product_payload(sku="CUP-5")
    payload["new_image"] = png_file()
    response = client.post(reverse("catalog:product_create"), payload)
    assert response.status_code == 302
    product = Product.objects.get(sku="CUP-5")
    assert product.images.count() == 1
    public = json.loads(
        client.get(reverse("core:landing")).content.decode().split('id="catalog-data" type="application/json">')[1].split("</script>")[0]
    )
    assert public[0]["customizable"] is True
    assert public[0]["image"]
