from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.crm.models import Contact, Opportunity
from apps.inventory.models import Expense, Ingredient, Investment, StockMovement
from apps.inventory.services import record_movement
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import register_payment
from apps.production.models import ProductionJob
from apps.quotations.models import Quote, QuoteRevision
from apps.quotations.services import accept_quote, send_quote
from apps.reports.services import period_result
from tests.factories import UserFactory


def make_contact():
    return Contact.objects.create(
        first_name="Luis",
        last_name="García",
        origin=Contact.Origin.WHATSAPP,
        whatsapp="5512345678",
    )


def make_product():
    category = Category.objects.create(name="Pasteles", slug="pasteles")
    return Product.objects.create(
        name="Pastel de vainilla",
        sku="PASTEL-VAINILLA",
        category=category,
        description="Betún de queso.",
        price_mode=Product.PriceMode.QUOTE,
        lead_time_days=3,
    )


def quote_payload(contact, product=None, **extra):
    event = timezone.localdate() + timedelta(days=10)
    payload = {
        "contact": contact.pk,
        "event_date": event.isoformat(),
        "event_time": "16:00",
        "delivery_type": Quote.Delivery.PICKUP,
        "discount": "50.00",
        "notes": "Sin nuez",
        "lines-TOTAL_FORMS": "1",
        "lines-INITIAL_FORMS": "0",
        "lines-MIN_NUM_FORMS": "0",
        "lines-MAX_NUM_FORMS": "1000",
        "lines-0-description": "Pastel de vainilla para 20",
        "lines-0-quantity": "2",
        "lines-0-unit_price": "450.00",
        "lines-0-product": product.pk if product else "",
    }
    payload.update(extra)
    return payload


@pytest.mark.django_db
def test_quote_totals_version_and_acceptance_create_order_and_job(client):
    sales = UserFactory(role=User.Role.VENTAS)
    contact = make_contact()
    product = make_product()
    opportunity = Opportunity.objects.create(contact=contact, title="Pastel de aniversario")
    client.force_login(sales)
    response = client.post(
        reverse("quotations:quote_create"),
        quote_payload(contact, product, opportunity=opportunity.pk),
    )
    quote = Quote.objects.get()
    assert response.status_code == 302
    assert quote.folio.endswith("-0001")
    assert quote.subtotal == Decimal("900.00")
    assert quote.total == Decimal("850.00")
    assert quote.status == Quote.Status.DRAFT
    opportunity.refresh_from_db()
    assert opportunity.stage == Opportunity.Stage.QUOTE_PENDING

    send_quote(quote, sales)
    quote.refresh_from_db()
    revision = QuoteRevision.objects.get()
    assert quote.status == Quote.Status.SENT
    assert quote.version == 1
    assert revision.snapshot["total"] == "850.00"
    assert revision.snapshot["lines"][0]["line_total"] == "900.00"

    line = quote.lines.get()
    client.post(
        reverse("quotations:quote_update", args=[quote.pk]),
        quote_payload(
            contact,
            product,
            discount="0.00",
            opportunity=opportunity.pk,
            **{
                "lines-INITIAL_FORMS": "1",
                "lines-0-id": line.pk,
            },
        ),
    )
    quote.refresh_from_db()
    assert quote.status == Quote.Status.DRAFT
    assert quote.total == Decimal("900.00")

    with pytest.raises(ValidationError):
        accept_quote(quote, sales)

    send_quote(quote, sales)
    quote.refresh_from_db()
    assert quote.version == 2
    order = accept_quote(quote, sales)
    quote.refresh_from_db()
    contact.refresh_from_db()
    opportunity.refresh_from_db()
    assert quote.status == Quote.Status.ACCEPTED
    assert order.folio.endswith("-0001")
    assert order.total == Decimal("900.00")
    assert order.quote_id == quote.pk
    assert contact.status == Contact.Status.CLIENT
    assert opportunity.stage == Opportunity.Stage.WON
    job = ProductionJob.objects.get()
    assert job.summary == "Pastel de vainilla para 20"
    assert job.scheduled_date == quote.event_date - timedelta(days=3)
    assert job.status == ProductionJob.Status.TODO


@pytest.mark.django_db
def test_payment_cannot_exceed_balance_and_kitchen_moves_the_order(client):
    sales = UserFactory(role=User.Role.VENTAS)
    baker = UserFactory(role=User.Role.PRODUCCION)
    contact = make_contact()
    client.force_login(sales)
    client.post(reverse("quotations:quote_create"), quote_payload(contact, discount="0.00"))
    quote = Quote.objects.get()
    send_quote(quote, sales)
    order = accept_quote(quote, sales)

    with pytest.raises(ValidationError):
        register_payment(
            order,
            amount=Decimal("900.01"),
            kind=Payment.Kind.DEPOSIT,
            method=Payment.Method.TRANSFER,
            paid_on=timezone.localdate(),
            note="",
            user=sales,
        )
    register_payment(
        order,
        amount=Decimal("400.00"),
        kind=Payment.Kind.DEPOSIT,
        method=Payment.Method.TRANSFER,
        paid_on=timezone.localdate(),
        note="",
        user=sales,
    )
    register_payment(
        order,
        amount=Decimal("500.00"),
        kind=Payment.Kind.SETTLEMENT,
        method=Payment.Method.CASH,
        paid_on=timezone.localdate(),
        note="",
        user=sales,
    )
    order.refresh_from_db()
    assert order.balance == Decimal("0.00")
    with pytest.raises(ValidationError):
        register_payment(
            order,
            amount=Decimal("0.01"),
            kind=Payment.Kind.SETTLEMENT,
            method=Payment.Method.CASH,
            paid_on=timezone.localdate(),
            note="",
            user=sales,
        )

    client.force_login(baker)
    job = order.jobs.get()
    response = client.post(
        reverse("production:job_detail", args=[job.pk]),
        {
            "scheduled_date": job.scheduled_date.isoformat(),
            "status": ProductionJob.Status.PREPARING,
            "decoration": "Flores de betún",
            "dedication": "Feliz aniversario",
            "warnings": "Sin nuez",
            "notes": "",
        },
    )
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == Order.Status.IN_PRODUCTION
    client.post(
        reverse("production:job_detail", args=[job.pk]),
        {
            "scheduled_date": job.scheduled_date.isoformat(),
            "status": ProductionJob.Status.READY,
            "decoration": "Flores de betún",
            "dedication": "Feliz aniversario",
            "warnings": "Sin nuez",
            "notes": "",
        },
    )
    order.refresh_from_db()
    assert order.status == Order.Status.READY

    denied = client.get(reverse("orders:order_detail", args=[order.pk]))
    assert denied.status_code == 403
    assert client.get(reverse("production:calendar")).status_code == 200


@pytest.mark.django_db
def test_purchase_average_and_period_result():
    admin = UserFactory(role=User.Role.ADMINISTRADOR)
    flour = Ingredient.objects.create(name="Harina", unit=Ingredient.Unit.GRAM, reorder_level=Decimal("500"))
    today = timezone.localdate()
    record_movement(
        flour,
        kind=StockMovement.Kind.PURCHASE,
        quantity=Decimal("1000"),
        unit_cost=Decimal("0.03"),
        occurred_on=today,
    )
    record_movement(
        flour,
        kind=StockMovement.Kind.PURCHASE,
        quantity=Decimal("1000"),
        unit_cost=Decimal("0.05"),
        occurred_on=today,
    )
    flour.refresh_from_db()
    assert flour.stock_quantity == Decimal("2000.000")
    assert flour.average_unit_cost == Decimal("0.0400")
    record_movement(
        flour,
        kind=StockMovement.Kind.WASTE,
        quantity=Decimal("100"),
        unit_cost=None,
        occurred_on=today,
    )
    flour.refresh_from_db()
    assert flour.stock_quantity == Decimal("1900.000")
    assert flour.average_unit_cost == Decimal("0.0400")
    with pytest.raises(ValidationError):
        record_movement(
            flour,
            kind=StockMovement.Kind.WASTE,
            quantity=Decimal("5000"),
            unit_cost=None,
            occurred_on=today,
        )

    Expense.objects.create(category=Expense.Category.RENT, amount=Decimal("500.00"), occurred_on=today)
    Investment.objects.create(name="Horno", amount=Decimal("10000.00"), acquired_on=today)
    contact = make_contact()
    order = Order.objects.create(
        folio="PED-PRUEBA-0001",
        contact=contact,
        event_at=timezone.now(),
        total=Decimal("1000.00"),
        subtotal=Decimal("1000.00"),
    )
    Payment.objects.create(
        order=order,
        kind=Payment.Kind.DEPOSIT,
        method=Payment.Method.TRANSFER,
        amount=Decimal("200.00"),
        paid_on=today,
        recorded_by=admin,
    )
    Payment.objects.create(
        order=order,
        kind=Payment.Kind.SETTLEMENT,
        method=Payment.Method.CASH,
        amount=Decimal("800.00"),
        paid_on=today,
        recorded_by=admin,
    )
    result = period_result(today, today)
    assert result["income"] == Decimal("1000.00")
    assert result["purchases"] == Decimal("80.00")
    assert result["expenses"] == Decimal("500.00")
    assert result["operating"] == Decimal("420.00")
    assert result["investment_total"] == Decimal("10000.00")
    assert result["after_investment"] == Decimal("-9580.00")


@pytest.mark.django_db
def test_roles_cannot_open_each_others_money(client):
    sales = UserFactory(role=User.Role.VENTAS)
    baker = UserFactory(role=User.Role.PRODUCCION)
    Ingredient.objects.create(
        name="Mantequilla",
        unit=Ingredient.Unit.GRAM,
        stock_quantity=Decimal("10"),
        average_unit_cost=Decimal("0.2500"),
    )
    client.force_login(sales)
    assert client.get(reverse("quotations:quote_list")).status_code == 200
    assert client.get(reverse("orders:calendar")).status_code == 200
    assert client.get(reverse("inventory:expense_list")).status_code == 403
    assert client.get(reverse("reports:result")).status_code == 403

    client.force_login(baker)
    assert client.get(reverse("quotations:quote_list")).status_code == 403
    assert client.get(reverse("orders:calendar")).status_code == 403
    stock = client.get(reverse("inventory:ingredient_list"))
    assert stock.status_code == 200
    body = stock.content.decode()
    assert "Mantequilla" in body
    assert "Costo promedio" not in body
    assert "0.2500" not in body
    assert client.get(reverse("reports:result")).status_code == 403


@pytest.mark.django_db
def test_calendar_lists_the_delivery_day(client):
    sales = UserFactory(role=User.Role.VENTAS)
    contact = make_contact()
    moment = timezone.make_aware(
        datetime.combine(date(2026, 12, 24), time(18, 0)),
        timezone.get_current_timezone(),
    )
    Order.objects.create(
        folio="PED-2026-0099",
        contact=contact,
        event_at=moment,
        status=Order.Status.CONFIRMED,
        total=Decimal("100.00"),
        subtotal=Decimal("100.00"),
        created_by=sales,
    )
    client.force_login(sales)
    response = client.get(reverse("orders:calendar"), {"anio": 2026, "mes": 12})
    body = response.content.decode()
    assert response.status_code == 200
    assert "PED-2026-0099" in body
    assert "diciembre 2026" in body
