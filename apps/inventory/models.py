"""Insumos, compras, gastos e inversiones del obrador."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Ingredient(models.Model):
    class Unit(models.TextChoices):
        GRAM = "g", "Gramos"
        KILOGRAM = "kg", "Kilogramos"
        MILLILITER = "ml", "Mililitros"
        LITER = "l", "Litros"
        PIECE = "pza", "Piezas"

    name = models.CharField("nombre", max_length=120, unique=True)
    unit = models.CharField("unidad", max_length=8, choices=Unit.choices)
    stock_quantity = models.DecimalField(
        "existencia",
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
    )
    average_unit_cost = models.DecimalField(
        "costo promedio",
        max_digits=12,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    reorder_level = models.DecimalField(
        "punto de reorden",
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "insumo"
        verbose_name_plural = "insumos"

    def __str__(self) -> str:
        return self.name

    @property
    def is_low(self) -> bool:
        return self.reorder_level > 0 and self.stock_quantity <= self.reorder_level


class StockMovement(models.Model):
    class Kind(models.TextChoices):
        PURCHASE = "compra", "Compra"
        WASTE = "merma", "Merma"
        ADJUSTMENT = "ajuste", "Ajuste"

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="insumo",
        related_name="movements",
        on_delete=models.PROTECT,
    )
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices)
    quantity = models.DecimalField("cantidad", max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(
        "costo unitario",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        "importe",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    occurred_on = models.DateField("fecha", db_index=True)
    note = models.CharField("nota", max_length=180, blank=True)

    class Meta:
        ordering = ["-occurred_on", "-pk"]
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.ingredient}"


class Expense(models.Model):
    class Category(models.TextChoices):
        RENT = "renta", "Renta"
        GAS = "gas", "Gas"
        PACKAGING = "empaque", "Empaque"
        SERVICES = "servicios", "Servicios"
        PAYROLL = "nomina", "Nómina"
        OTHER = "otro", "Otro"

    category = models.CharField("categoría", max_length=20, choices=Category.choices)
    amount = models.DecimalField(
        "importe",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    occurred_on = models.DateField("fecha", db_index=True)
    note = models.CharField("nota", max_length=180, blank=True)

    class Meta:
        ordering = ["-occurred_on", "-pk"]
        verbose_name = "gasto"
        verbose_name_plural = "gastos"

    def __str__(self) -> str:
        return f"{self.get_category_display()} {self.amount}"


class Investment(models.Model):
    name = models.CharField("equipo", max_length=140)
    amount = models.DecimalField(
        "importe",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    acquired_on = models.DateField("fecha de compra", db_index=True)
    note = models.CharField("nota", max_length=180, blank=True)

    class Meta:
        ordering = ["-acquired_on", "-pk"]
        verbose_name = "inversión"
        verbose_name_plural = "inversiones"

    def __str__(self) -> str:
        return self.name
