"""Fichas del obrador. Una por cada pieza del pedido."""

from django.db import models


class ProductionJob(models.Model):
    class Status(models.TextChoices):
        TODO = "por_hacer", "Por hacer"
        PREPARING = "en_preparacion", "En preparación"
        DECORATING = "decorando", "Decorando"
        READY = "listo", "Listo"

    order = models.ForeignKey(
        "orders.Order",
        verbose_name="pedido",
        related_name="jobs",
        on_delete=models.CASCADE,
    )
    order_line = models.OneToOneField(
        "orders.OrderLine",
        verbose_name="partida",
        related_name="job",
        on_delete=models.CASCADE,
    )
    summary = models.CharField("pieza", max_length=240)
    scheduled_date = models.DateField("día de preparación", db_index=True)
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    decoration = models.CharField("decoración", max_length=180, blank=True)
    dedication = models.CharField("dedicatoria", max_length=180, blank=True)
    warnings = models.TextField("advertencias", blank=True)
    notes = models.TextField("notas de cocina", blank=True)

    class Meta:
        ordering = ["scheduled_date", "pk"]
        verbose_name = "ficha de producción"
        verbose_name_plural = "fichas de producción"

    def __str__(self) -> str:
        return self.summary
