"""Importes de la repostería, siempre en Decimal y a centavos."""

from decimal import Decimal

TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")


def money(value) -> Decimal:
    return Decimal(value).quantize(TWOPLACES)


def pesos(value) -> str:
    amount = money(value)
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"
