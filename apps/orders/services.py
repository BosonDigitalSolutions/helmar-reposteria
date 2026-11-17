"""Creación de pedidos y recálculo de totales."""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.folios import next_folio
from apps.core.money import money
from apps.orders.models import Order, OrderLine
from apps.production.services import create_jobs


def aware_event(day, clock) -> datetime:
    combined = datetime.combine(day, clock)
    return timezone.make_aware(combined, timezone.get_current_timezone())


def refresh_totals(order: Order) -> Order:
    subtotal = Decimal_sum(order)
    if order.discount > subtotal:
        raise ValidationError({"discount": "El descuento no puede superar el subtotal."})
    order.subtotal = subtotal
    order.total = money(subtotal - order.discount)
    order.save(update_fields=["subtotal", "total", "updated_at"])
    return order


def Decimal_sum(order: Order):
    total = order.lines.aggregate(total=Sum("line_total"))["total"]
    return money(total or 0)


def create_order_from_quote(quote, user) -> Order:
    with transaction.atomic():
        order = Order.objects.create(
            folio=next_folio("PED"),
            quote=quote,
            contact=quote.contact,
            status=Order.Status.CONFIRMED,
            event_at=aware_event(quote.event_date, quote.event_time),
            delivery_type=quote.delivery_type,
            address=quote.address,
            notes=quote.notes,
            discount=quote.discount,
            created_by=user,
        )
        for line in quote.lines.all():
            OrderLine.objects.create(
                order=order,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
        refresh_totals(order)
        create_jobs(order)
    return order
