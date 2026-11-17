"""Productos publicados en el catálogo de HelyMar."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("nombre", max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    display_order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    class PriceMode(models.TextChoices):
        FROM_BASE = "desde", "Desde un precio base"
        QUOTE = "cotizacion", "Sujeto a cotización"

    name = models.CharField("nombre", max_length=140)
    sku = models.CharField("SKU", max_length=40, unique=True)
    category = models.ForeignKey(
        Category,
        verbose_name="categoría",
        related_name="products",
        on_delete=models.PROTECT,
    )
    description = models.TextField("descripción")
    price_mode = models.CharField(
        "tipo de precio",
        max_length=20,
        choices=PriceMode.choices,
        default=PriceMode.QUOTE,
    )
    base_price = models.DecimalField(
        "precio base",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    is_active = models.BooleanField("activo", default=True)
    is_customizable = models.BooleanField("personalizable", default=False)
    lead_time_days = models.PositiveIntegerField(
        "anticipación mínima (días)",
        help_text="Días mínimos antes de la fecha solicitada.",
    )
    display_order = models.PositiveIntegerField("orden de visualización", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        if self.price_mode == self.PriceMode.FROM_BASE and self.base_price is None:
            raise ValidationError(
                {"base_price": "Indica el precio base cuando el producto se vende desde un importe."}
            )
        if self.price_mode == self.PriceMode.QUOTE and self.base_price is not None:
            raise ValidationError(
                {"base_price": "Un producto sujeto a cotización no lleva precio base."}
            )

    @property
    def price_label(self) -> str:
        if self.price_mode == self.PriceMode.QUOTE or self.base_price is None:
            return "Sujeto a cotización"
        amount = self.base_price.quantize(Decimal("0.01"))
        return f"Desde ${amount:,.2f}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="producto",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("imagen", upload_to="catalog/products/")
    alt_text = models.CharField("texto alternativo", max_length=140, blank=True)
    display_order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["display_order", "pk"]
        verbose_name = "fotografía"
        verbose_name_plural = "fotografías"

    def __str__(self) -> str:
        return self.alt_text or f"Imagen de {self.product}"


class ProductPresentation(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="producto",
        related_name="presentations",
        on_delete=models.CASCADE,
    )
    name = models.CharField("presentación", max_length=80)
    display_order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "presentación"
        verbose_name_plural = "presentaciones"

    def __str__(self) -> str:
        return self.name


class ProductCustomization(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="producto",
        related_name="customizations",
        on_delete=models.CASCADE,
    )
    name = models.CharField("opción", max_length=80)
    display_order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "opción de personalización"
        verbose_name_plural = "opciones de personalización"

    def __str__(self) -> str:
        return self.name
