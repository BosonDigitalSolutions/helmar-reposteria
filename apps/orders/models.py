"""Pedidos confirmados, con fecha y hora de entrega."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from apps.core.money import money
from apps.quotations.models import Quote


class Order(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmado", "Confirmado"
        IN_PRODUCTION = "en_produccion", "En producción"
        READY = "listo", "Listo"
        DELIVERED = "entregado", "Entregado"
        CANCELLED = "cancelado", "Cancelado"

    folio = models.CharField("folio", max_length=20, unique=True)
    quote = models.OneToOneField(
        Quote,
        verbose_name="cotización",
        related_name="order",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    contact = models.ForeignKey(
        "crm.Contact",
        verbose_name="contacto",
        related_name="orders",
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    event_at = models.DateTimeField("entrega", db_index=True)
    delivery_type = models.CharField(
        "entrega",
        max_length=20,
        choices=Quote.Delivery.choices,
        default=Quote.Delivery.PICKUP,
    )
    address = models.CharField("dirección", max_length=240, blank=True)
    notes = models.TextField("notas", blank=True)
    discount = models.DecimalField(
        "descuento",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal = models.DecimalField(
        "subtotal",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        "total",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="creado por",
        related_name="orders_created",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_at", "folio"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self) -> str:
        return self.folio

    @property
    def amount_paid(self) -> Decimal:
        paid = self.payments.aggregate(total=Sum("amount"))["total"]
        return money(paid or 0)

    @property
    def balance(self) -> Decimal:
        return money(self.total - self.amount_paid)

    @property
    def is_open(self) -> bool:
        return self.status not in {self.Status.DELIVERED, self.Status.CANCELLED}


class OrderLine(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="pedido",
        related_name="lines",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="producto",
        related_name="order_lines",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    description = models.CharField("descripción", max_length=240)
    quantity = models.DecimalField(
        "cantidad",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        "precio unitario",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    line_total = models.DecimalField(
        "importe",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["pk"]
        verbose_name = "partida de pedido"
        verbose_name_plural = "partidas de pedido"

    def __str__(self) -> str:
        return self.description

    def save(self, *args, **kwargs):
        from apps.core.money import money as quantize

        self.line_total = quantize(self.quantity * self.unit_price)
        super().save(*args, **kwargs)
