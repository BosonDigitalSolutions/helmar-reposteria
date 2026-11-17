"""Compras, mermas y ajustes. El horno no descuenta stock solo."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.money import FOURPLACES, money
from apps.inventory.models import Ingredient, StockMovement


def record_movement(ingredient, *, kind, quantity, unit_cost, occurred_on, note="") -> StockMovement:
    quantity = Decimal(quantity)
    with transaction.atomic():
        locked = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
        cost = None
        amount = Decimal("0.00")
        if kind == StockMovement.Kind.PURCHASE:
            if quantity <= 0:
                raise ValidationError({"quantity": "La compra debe ser mayor a cero."})
            if unit_cost is None or Decimal(unit_cost) < 0:
                raise ValidationError({"unit_cost": "Indica el costo por unidad del insumo."})
            cost = Decimal(unit_cost).quantize(FOURPLACES)
            new_stock = locked.stock_quantity + quantity
            total_cost = locked.stock_quantity * locked.average_unit_cost + quantity * cost
            locked.average_unit_cost = (total_cost / new_stock).quantize(FOURPLACES)
            locked.stock_quantity = new_stock
            amount = money(quantity * cost)
        elif kind == StockMovement.Kind.WASTE:
            if quantity <= 0:
                raise ValidationError({"quantity": "La merma debe ser mayor a cero."})
            if quantity > locked.stock_quantity:
                raise ValidationError({"quantity": "La merma supera la existencia."})
            locked.stock_quantity -= quantity
            cost = locked.average_unit_cost
        elif kind == StockMovement.Kind.ADJUSTMENT:
            if quantity == 0:
                raise ValidationError({"quantity": "El ajuste no puede ser cero."})
            new_stock = locked.stock_quantity + quantity
            if new_stock < 0:
                raise ValidationError({"quantity": "El ajuste dejaría la existencia en negativo."})
            locked.stock_quantity = new_stock
        else:
            raise ValidationError("El tipo de movimiento no es válido.")
        locked.save(update_fields=["stock_quantity", "average_unit_cost"])
        return StockMovement.objects.create(
            ingredient=locked,
            kind=kind,
            quantity=quantity,
            unit_cost=cost,
            amount=amount,
            occurred_on=occurred_on,
            note=note or "",
        )
