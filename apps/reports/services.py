"""Resultado del periodo: cobros, compras, gastos e inversiones."""

from django.db.models import Sum

from apps.core.money import money
from apps.inventory.models import Expense, Investment, StockMovement
from apps.payments.models import Payment


def period_result(start, end) -> dict:
    income = Payment.objects.filter(paid_on__range=(start, end)).aggregate(total=Sum("amount"))["total"]
    purchases = StockMovement.objects.filter(
        kind=StockMovement.Kind.PURCHASE,
        occurred_on__range=(start, end),
    ).aggregate(total=Sum("amount"))["total"]
    expenses = Expense.objects.filter(occurred_on__range=(start, end)).aggregate(total=Sum("amount"))[
        "total"
    ]
    investments = Investment.objects.filter(acquired_on__range=(start, end))
    investment_total = investments.aggregate(total=Sum("amount"))["total"]
    income = money(income or 0)
    purchases = money(purchases or 0)
    expenses = money(expenses or 0)
    investment_total = money(investment_total or 0)
    operating = money(income - purchases - expenses)
    return {
        "income": income,
        "purchases": purchases,
        "expenses": expenses,
        "operating": operating,
        "investments": investments,
        "investment_total": investment_total,
        "after_investment": money(operating - investment_total),
    }
