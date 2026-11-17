import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.crm.models import Contact, Opportunity, OpportunityStageLog
from tests.factories import UserFactory


def contact_payload(**overrides):
    payload = {
        "first_name": "María",
        "last_name": "López",
        "email": "maria@example.com",
        "phone": "55 1000 0001",
        "whatsapp": "",
        "company": "",
        "origin": Contact.Origin.WHATSAPP,
        "status": Contact.Status.LEAD,
        "observations": "",
        "owner": "",
        "next_follow_up": "",
        "tags_text": "xv, familiar",
    }
    payload.update(overrides)
    return payload


def csv_file(text, name="contactos.csv"):
    return SimpleUploadedFile(name, text.encode("utf-8"), content_type="text/csv")


@pytest.mark.django_db
def test_sales_creates_contact_and_production_cannot(client):
    sales = UserFactory(role=User.Role.VENTAS, password="clave-segura-123")
    client.force_login(sales)
    response = client.post(reverse("crm:contact_create"), contact_payload())
    assert response.status_code == 302
    contact = Contact.objects.get(email="maria@example.com")
    assert contact.status == Contact.Status.LEAD
    assert set(contact.tags.values_list("name", flat=True)) == {"xv", "familiar"}

    production = UserFactory(role=User.Role.PRODUCCION)
    client.force_login(production)
    assert client.get(reverse("crm:contact_list")).status_code == 403


@pytest.mark.django_db
def test_winning_an_opportunity_does_not_make_a_client(client):
    sales = UserFactory(role=User.Role.VENTAS)
    client.force_login(sales)
    contact = Contact.objects.create(
        first_name="Luis",
        last_name="Pérez",
        email="luis@example.com",
        origin=Contact.Origin.REFERRAL,
        status=Contact.Status.PROSPECT,
        owner=sales,
    )
    response = client.post(
        reverse("crm:opportunity_create"),
        {
            "title": "Mesa de postres",
            "contact": contact.pk,
            "owner": sales.pk,
            "stage": Opportunity.Stage.NEW,
        },
    )
    assert response.status_code == 302
    opportunity = Opportunity.objects.get(title="Mesa de postres")
    moved = client.post(
        reverse("crm:opportunity_move", args=[opportunity.pk]),
        {"stage": Opportunity.Stage.WON},
    )
    assert moved.status_code == 302
    contact.refresh_from_db()
    opportunity.refresh_from_db()
    assert contact.status == Contact.Status.PROSPECT
    assert opportunity.stage == Opportunity.Stage.WON
    assert OpportunityStageLog.objects.filter(
        opportunity=opportunity,
        to_stage=Opportunity.Stage.WON,
    ).exists()


@pytest.mark.django_db
def test_csv_preview_detects_duplicates_and_does_not_merge(client):
    sales = UserFactory(role=User.Role.VENTAS)
    client.force_login(sales)
    Contact.objects.create(
        first_name="Ana",
        last_name="Rivas",
        email="ana@example.com",
        phone="5511111111",
        origin=Contact.Origin.COUNTER,
        status=Contact.Status.CLIENT,
    )
    uploaded = csv_file(
        "nombre,apellidos,correo,telefono,whatsapp,empresa,origen,estado,etiquetas,observaciones\n"
        "Ana,Otra,ana@example.com,5599999999,,,whatsapp,lead,,\n"
        "Beto,Cruz,beto@example.com,5511111111,,,referido,prospecto,,\n"
        "Nuevo,Contacto,nuevo@example.com,5522222222,,,instagram,lead,boda,\n"
    )
    preview = client.post(reverse("crm:import_upload"), {"archivo": uploaded})
    assert preview.status_code == 302
    preview_page = client.get(preview.url)
    body = preview_page.content.decode()
    assert "Ya existe un contacto" in body
    assert "Nuevo" in body
    assert Contact.objects.filter(email="nuevo@example.com").count() == 0

    from apps.crm.models import ImportBatch, ImportRow

    batch = ImportBatch.objects.latest("created_at")
    duplicate = ImportRow.objects.get(batch=batch, line_number=2)
    phone_duplicate = ImportRow.objects.get(batch=batch, line_number=3)
    fresh = ImportRow.objects.get(batch=batch, line_number=4)
    assert duplicate.action == ImportRow.Action.SKIP
    assert phone_duplicate.is_duplicate
    confirmed = client.post(
        reverse("crm:import_confirm", args=[batch.pk]),
        {
            f"action-{duplicate.pk}": "crear",
            f"action-{phone_duplicate.pk}": "omitir",
            f"action-{fresh.pk}": "crear",
        },
    )
    assert confirmed.status_code == 302
    assert Contact.objects.filter(email="ana@example.com").count() == 2
    original = Contact.objects.get(email="ana@example.com", last_name="Rivas")
    assert original.last_name == "Rivas"
    assert Contact.objects.filter(email="nuevo@example.com", status=Contact.Status.LEAD).exists()
    assert not Contact.objects.filter(email="beto@example.com").exists()


@pytest.mark.django_db
def test_ambiguous_matches_are_not_merged(client):
    sales = UserFactory(role=User.Role.VENTAS)
    client.force_login(sales)
    Contact.objects.create(
        first_name="Correo",
        email="mixto@example.com",
        phone="5500000001",
        origin=Contact.Origin.OTHER,
    )
    Contact.objects.create(
        first_name="Telefono",
        email="otro@example.com",
        phone="5500000002",
        origin=Contact.Origin.OTHER,
    )
    uploaded = csv_file(
        "nombre,correo,telefono,origen\n"
        "Mixto,mixto@example.com,5500000002,whatsapp\n"
    )
    preview = client.post(reverse("crm:import_upload"), {"archivo": uploaded})
    page = client.get(preview.url)
    assert "No se fusionará" in page.content.decode()
    from apps.crm.models import ImportBatch

    batch = ImportBatch.objects.latest("created_at")
    client.post(reverse("crm:import_confirm", args=[batch.pk]), {})
    assert Contact.objects.count() == 2
    assert Contact.objects.get(email="mixto@example.com").first_name == "Correo"
    assert Contact.objects.get(phone="5500000002").first_name == "Telefono"
