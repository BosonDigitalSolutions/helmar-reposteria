"""Cobros que no pueden rebasar el saldo del pedido."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.core.money import money
from apps.orders.models import Order
from apps.payments.models import Payment


def register_payment(order, *, amount, kind, method, paid_on, note, user) -> Payment:
    amount = money(amount)
    if amount <= 0:
        raise ValidationError({"amount": "El importe debe ser mayor a cero."})
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.status == Order.Status.CANCELLED:
            raise ValidationError("Un pedido cancelado no se cobra.")
        paid = locked.payments.aggregate(total=Sum("amount"))["total"]
        balance = money(locked.total - money(paid or 0))
        if amount > balance:
            raise ValidationError({"amount": "El cobro supera el saldo."})
        return Payment.objects.create(
            order=locked,
            amount=amount,
            kind=kind,
            method=method,
            paid_on=paid_on,
            note=note or "",
            recorded_by=user,
        )
