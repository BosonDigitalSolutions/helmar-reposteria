"""Partidas de cotización y pedido."""

from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.core.money import money


def clean_line(cleaned):
    if not cleaned or cleaned.get("DELETE"):
        return cleaned
    product = cleaned.get("product")
    description = (cleaned.get("description") or "").strip()
    quantity = cleaned.get("quantity")
    unit_price = cleaned.get("unit_price")
    if product is None and not description and quantity is None and unit_price is None:
        return cleaned
    if not description and product is not None:
        description = product.name
    if not description:
        raise ValidationError("Describe la partida.")
    if quantity is None or quantity <= 0:
        raise ValidationError("Indica una cantidad mayor a cero.")
    if unit_price is None or unit_price <= 0:
        raise ValidationError("Indica un precio mayor a cero.")
    cleaned["description"] = description
    cleaned["quantity"] = quantity
    cleaned["unit_price"] = money(unit_price)
    return cleaned


def active_lines(formset):
    lines = []
    for form in formset.forms:
        data = getattr(form, "cleaned_data", None) or {}
        if not data or data.get("DELETE") or not data.get("description"):
            continue
        lines.append(data)
    return lines


def subtotal_from_lines(lines) -> Decimal:
    total = Decimal("0.00")
    for line in lines:
        total += money(line["quantity"] * line["unit_price"])
    return total
