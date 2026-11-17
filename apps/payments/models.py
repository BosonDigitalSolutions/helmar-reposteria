"""Anticipos y liquidaciones registrados por el personal."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Payment(models.Model):
    class Kind(models.TextChoices):
        DEPOSIT = "anticipo", "Anticipo"
        SETTLEMENT = "liquidacion", "Liquidación"

    class Method(models.TextChoices):
        CASH = "efectivo", "Efectivo"
        TRANSFER = "transferencia", "Transferencia"
        OTHER = "otro", "Otro"

    order = models.ForeignKey(
        "orders.Order",
        verbose_name="pedido",
        related_name="payments",
        on_delete=models.PROTECT,
    )
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices)
    method = models.CharField("método", max_length=20, choices=Method.choices)
    amount = models.DecimalField(
        "importe",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    paid_on = models.DateField("fecha de cobro", db_index=True)
    note = models.CharField("nota", max_length=180, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["paid_on", "pk"]
        verbose_name = "cobro"
        verbose_name_plural = "cobros"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.amount}"
