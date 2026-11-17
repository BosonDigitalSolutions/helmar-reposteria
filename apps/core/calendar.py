"""Calendario mensual de lunes a domingo, sin librerías externas."""

import calendar
from datetime import date

MONTHS = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
WEEKDAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_label(year: int, month: int) -> str:
    return f"{MONTHS[month]} {year}"


def month_days(year: int, month: int) -> list[list[date]]:
    return calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
