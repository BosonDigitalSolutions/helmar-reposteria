"""Usuario del personal de HelyMar."""

from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models

from .roles import ROLE_GROUP_NAMES


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        VENTAS = "ventas", "Ventas"
        PRODUCCION = "produccion", "Producción"

    role = models.CharField(
        "rol",
        max_length=32,
        choices=Role.choices,
        help_text="Valores: administrador, ventas o produccion.",
    )

    REQUIRED_FIELDS = ["email", "role"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def clean(self):
        super().clean()
        self.role = self.normalize_role(self.role)
        if self.role not in self.Role.values:
            raise ValidationError(
                {"role": "Selecciona administrador, ventas o produccion."}
            )

    def save(self, *args, **kwargs):
        self.role = self.normalize_role(self.role)
        if self.role not in self.Role.values:
            raise ValueError("El rol debe ser administrador, ventas o produccion.")
        if self.role == self.Role.ADMINISTRADOR:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)
        update_fields = kwargs.get("update_fields")
        if update_fields is None or "role" in update_fields:
            self.sync_role_group()

    @classmethod
    def normalize_role(cls, role: str) -> str:
        if not isinstance(role, str):
            return role
        aliases = {
            "administrador": cls.Role.ADMINISTRADOR,
            "admin": cls.Role.ADMINISTRADOR,
            "ventas": cls.Role.VENTAS,
            "produccion": cls.Role.PRODUCCION,
            "producción": cls.Role.PRODUCCION,
        }
        return aliases.get(role.strip().lower(), role.strip().lower())

    def sync_role_group(self) -> None:
        target_name = ROLE_GROUP_NAMES[self.role]
        target, _created = Group.objects.get_or_create(name=target_name)
        stale = list(
            Group.objects.filter(name__in=ROLE_GROUP_NAMES.values()).exclude(pk=target.pk)
        )
        if stale:
            self.groups.remove(*stale)
        self.groups.add(target)
