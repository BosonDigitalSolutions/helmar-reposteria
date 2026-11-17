"""Cotizaciones que se envían antes de comprometer el horno."""

from datetime import time
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.money import money


class Quote(models.Model):
    class Status(models.TextChoices):
        DRAFT = "borrador", "Borrador"
        SENT = "enviada", "Enviada"
        ACCEPTED = "aceptada", "Aceptada"
        REJECTED = "rechazada", "Rechazada"
        EXPIRED = "vencida", "Vencida"

    class Delivery(models.TextChoices):
        PICKUP = "recoger", "Recoger en obrador"
        SHIP = "enviar", "Enviar"

    folio = models.CharField("folio", max_length=20, unique=True)
    contact = models.ForeignKey(
        "crm.Contact",
        verbose_name="contacto",
        related_name="quotes",
        on_delete=models.PROTECT,
    )
    opportunity = models.ForeignKey(
        "crm.Opportunity",
        verbose_name="oportunidad",
        related_name="quotes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    version = models.PositiveIntegerField("versión enviada", default=0)
    event_date = models.DateField("fecha del evento")
    event_time = models.TimeField("hora del evento", default=time(12, 0))
    valid_until = models.DateField("vigencia", null=True, blank=True)
    delivery_type = models.CharField(
        "entrega",
        max_length=20,
        choices=Delivery.choices,
        default=Delivery.PICKUP,
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
        verbose_name="creada por",
        related_name="quotes_created",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"

    def __str__(self) -> str:
        return self.folio

    @property
    def is_editable(self) -> bool:
        return self.status in {self.Status.DRAFT, self.Status.SENT}


class QuoteLine(models.Model):
    quote = models.ForeignKey(
        Quote,
        verbose_name="cotización",
        related_name="lines",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="producto",
        related_name="quote_lines",
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
        verbose_name = "partida de cotización"
        verbose_name_plural = "partidas de cotización"

    def __str__(self) -> str:
        return self.description

    def save(self, *args, **kwargs):
        self.line_total = money(self.quantity * self.unit_price)
        super().save(*args, **kwargs)


class QuoteRevision(models.Model):
    quote = models.ForeignKey(
        Quote,
        verbose_name="cotización",
        related_name="revisions",
        on_delete=models.CASCADE,
    )
    number = models.PositiveIntegerField("versión")
    snapshot = models.JSONField("versión congelada")
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="enviada por",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-number"]
        constraints = [
            models.UniqueConstraint(fields=["quote", "number"], name="unique_quote_version"),
        ]
        verbose_name = "versión de cotización"
        verbose_name_plural = "versiones de cotización"

    def __str__(self) -> str:
        return f"{self.quote.folio} v{self.number}"
