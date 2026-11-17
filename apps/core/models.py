"""Secuencias de folio compartidas por cotizaciones y pedidos."""

from django.db import models


class FolioSequence(models.Model):
    prefix = models.CharField(max_length=8)
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["prefix", "year"], name="unique_folio_year"),
        ]
        verbose_name = "secuencia de folio"
        verbose_name_plural = "secuencias de folio"

    def __str__(self) -> str:
        return f"{self.prefix}-{self.year}"
