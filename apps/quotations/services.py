"""Envío, versiones y aceptación de una cotización."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.money import money, pesos
from apps.crm.models import Contact, ContactStatusLog, Opportunity, OpportunityStageLog
from apps.orders.services import create_order_from_quote
from apps.quotations.models import Quote, QuoteRevision


def refresh_totals(quote: Quote) -> Quote:
    subtotal = quote.lines.aggregate(total=Sum("line_total"))["total"]
    subtotal = money(subtotal or 0)
    if quote.discount > subtotal:
        raise ValidationError({"discount": "El descuento no puede superar el subtotal."})
    quote.subtotal = subtotal
    quote.total = money(subtotal - quote.discount)
    quote.save(update_fields=["subtotal", "total", "updated_at"])
    return quote


def rush_warning(quote: Quote) -> str:
    days_until = (quote.event_date - timezone.localdate()).days
    needed = [
        line.product.lead_time_days
        for line in quote.lines.select_related("product")
        if line.product_id
    ]
    if not needed:
        return ""
    minimum = max(needed)
    if days_until < minimum:
        return (
            f"La fecha está a {days_until} días y hay una pieza que pide "
            f"{minimum} de anticipación. El obrador decide si la acepta."
        )
    return ""


def whatsapp_message(quote: Quote) -> str:
    rows = []
    for line in quote.lines.all():
        rows.append(
            f"- {line.description}: {line.quantity} x {pesos(line.unit_price)} = {pesos(line.line_total)}"
        )
    validity = ""
    if quote.valid_until:
        validity = f"Vigencia: {quote.valid_until.strftime('%d/%m/%Y')}\n"
    return (
        f"Hola {quote.contact.first_name}, te comparto la cotización {quote.folio} de HelyMar.\n"
        f"{chr(10).join(rows)}\n"
        f"Subtotal: {pesos(quote.subtotal)}\n"
        f"Descuento: {pesos(quote.discount)}\n"
        f"Total: {pesos(quote.total)}\n"
        f"Fecha del evento: {quote.event_date.strftime('%d/%m/%Y')} {quote.event_time.strftime('%H:%M')}\n"
        f"Entrega: {quote.get_delivery_type_display()}\n"
        f"{validity}"
    ).strip()


def _move_opportunity(opportunity, stage, user):
    if opportunity is None or opportunity.stage == stage:
        return
    if opportunity.stage in {Opportunity.Stage.WON, Opportunity.Stage.LOST}:
        return
    previous = opportunity.stage
    opportunity.stage = stage
    opportunity.save(update_fields=["stage", "updated_at"])
    OpportunityStageLog.objects.create(
        opportunity=opportunity,
        from_stage=previous,
        to_stage=stage,
        changed_by=user,
    )


def mark_quote_pending(quote: Quote, user):
    early = {
        Opportunity.Stage.NEW,
        Opportunity.Stage.CONTACTED,
        Opportunity.Stage.INTERESTED,
    }
    if quote.opportunity_id and quote.opportunity.stage in early:
        _move_opportunity(quote.opportunity, Opportunity.Stage.QUOTE_PENDING, user)


def snapshot(quote: Quote, number: int) -> dict:
    return {
        "folio": quote.folio,
        "version": number,
        "contact": quote.contact.full_name,
        "event_date": quote.event_date.isoformat(),
        "event_time": quote.event_time.isoformat(),
        "delivery_type": quote.delivery_type,
        "discount": str(quote.discount),
        "subtotal": str(quote.subtotal),
        "total": str(quote.total),
        "lines": [
            {
                "description": line.description,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "line_total": str(line.line_total),
            }
            for line in quote.lines.all()
        ],
    }


def send_quote(quote: Quote, user) -> QuoteRevision:
    with transaction.atomic():
        quote = Quote.objects.select_for_update().get(pk=quote.pk)
        if quote.status != Quote.Status.DRAFT:
            raise ValidationError("Solo se envía una cotización en borrador.")
        if not quote.lines.exists():
            raise ValidationError("Agrega al menos una partida.")
        refresh_totals(quote)
        number = quote.version + 1
        revision = QuoteRevision.objects.create(
            quote=quote,
            number=number,
            snapshot=snapshot(quote, number),
            sent_by=user,
        )
        quote.status = Quote.Status.SENT
        quote.version = number
        quote.save(update_fields=["status", "version", "updated_at"])
        _move_opportunity(quote.opportunity, Opportunity.Stage.QUOTE_SENT, user)
    return revision


def accept_quote(quote: Quote, user):
    with transaction.atomic():
        quote = Quote.objects.select_for_update().get(pk=quote.pk)
        if quote.status != Quote.Status.SENT:
            raise ValidationError("Solo se acepta una cotización enviada.")
        latest = quote.revisions.order_by("-number").first()
        if latest is None or latest.number != quote.version:
            raise ValidationError("La versión enviada no coincide.")
        if quote.valid_until and quote.valid_until < timezone.localdate():
            raise ValidationError("La cotización está vencida.")
        from apps.orders.models import Order

        if Order.objects.filter(quote=quote).exists():
            raise ValidationError("Esta cotización ya tiene un pedido.")
        order = create_order_from_quote(quote, user)
        quote.status = Quote.Status.ACCEPTED
        quote.save(update_fields=["status", "updated_at"])
        _move_opportunity(quote.opportunity, Opportunity.Stage.WON, user)
        contact = Contact.objects.select_for_update().get(pk=quote.contact_id)
        if contact.status != Contact.Status.CLIENT:
            previous = contact.status
            contact.status = Contact.Status.CLIENT
            contact.save(update_fields=["status"])
            ContactStatusLog.objects.create(
                contact=contact,
                from_status=previous,
                to_status=contact.status,
                changed_by=user,
            )
    return order


def reject_quote(quote: Quote, user) -> Quote:
    with transaction.atomic():
        quote = Quote.objects.select_for_update().get(pk=quote.pk)
        if quote.status != Quote.Status.SENT:
            raise ValidationError("Solo se rechaza una cotización enviada.")
        quote.status = Quote.Status.REJECTED
        quote.save(update_fields=["status", "updated_at"])
    return quote


def expire_quote(quote: Quote, user) -> Quote:
    with transaction.atomic():
        quote = Quote.objects.select_for_update().get(pk=quote.pk)
        if quote.status != Quote.Status.SENT:
            raise ValidationError("Solo se vence una cotización enviada.")
        quote.status = Quote.Status.EXPIRED
        quote.save(update_fields=["status", "updated_at"])
    return quote
