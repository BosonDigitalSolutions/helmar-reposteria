"""Contactos y oportunidades comerciales de HelyMar."""

from django.conf import settings
from django.db import models

from .normalization import digits, normalize_email


class Tag(models.Model):
    name = models.CharField("nombre", max_length=40, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class CrmSettings(models.Model):
    match_email = models.BooleanField("detectar duplicados por correo", default=True)
    match_phone = models.BooleanField("detectar duplicados por teléfono", default=True)

    class Meta:
        verbose_name = "regla de duplicados"
        verbose_name_plural = "reglas de duplicados"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        settings_row, _created = cls.objects.get_or_create(pk=1)
        return settings_row


class Contact(models.Model):
    class Status(models.TextChoices):
        LEAD = "lead", "Lead"
        PROSPECT = "prospecto", "Prospecto"
        CLIENT = "cliente", "Cliente"

    class Origin(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        REFERRAL = "referido", "Referido"
        COUNTER = "mostrador", "Mostrador"
        OTHER = "otro", "Otro"

    first_name = models.CharField("nombre", max_length=80)
    last_name = models.CharField("apellidos", max_length=80, blank=True)
    email = models.EmailField("correo electrónico", blank=True, db_index=True)
    phone = models.CharField("teléfono", max_length=30, blank=True, db_index=True)
    whatsapp = models.CharField("WhatsApp", max_length=30, blank=True)
    company = models.CharField("empresa", max_length=120, blank=True)
    origin = models.CharField("origen", max_length=20, choices=Origin.choices)
    registered_at = models.DateTimeField("fecha de registro", auto_now_add=True)
    status = models.CharField(
        "estado comercial",
        max_length=20,
        choices=Status.choices,
        default=Status.LEAD,
    )
    tags = models.ManyToManyField(Tag, verbose_name="etiquetas", blank=True)
    observations = models.TextField("observaciones", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="responsable comercial",
        related_name="assigned_contacts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    next_follow_up = models.DateField("próximo seguimiento", null=True, blank=True)
    normalized_email = models.CharField(max_length=254, blank=True, db_index=True)
    normalized_phone = models.CharField(max_length=30, blank=True, db_index=True)
    normalized_whatsapp = models.CharField(max_length=30, blank=True, db_index=True)

    class Meta:
        ordering = ["-registered_at"]
        verbose_name = "contacto"
        verbose_name_plural = "contactos"

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        self.normalized_email = normalize_email(self.email)
        self.normalized_phone = digits(self.phone)
        self.normalized_whatsapp = digits(self.whatsapp)
        super().save(*args, **kwargs)


class ContactStatusLog(models.Model):
    contact = models.ForeignKey(
        Contact,
        related_name="status_logs",
        on_delete=models.CASCADE,
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "cambio de estado del contacto"
        verbose_name_plural = "cambios de estado del contacto"


class Note(models.Model):
    contact = models.ForeignKey(Contact, related_name="notes", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    body = models.TextField("nota")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "nota comercial"
        verbose_name_plural = "notas comerciales"


class Activity(models.Model):
    contact = models.ForeignKey(Contact, related_name="activities", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    summary = models.CharField("actividad", max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "actividad"
        verbose_name_plural = "actividades"


class Opportunity(models.Model):
    class Stage(models.TextChoices):
        NEW = "nuevo_contacto", "Nuevo contacto"
        CONTACTED = "contactado", "Contactado"
        INTERESTED = "interesado", "Interesado"
        QUOTE_PENDING = "cotizacion_pendiente", "Cotización pendiente"
        QUOTE_SENT = "cotizacion_enviada", "Cotización enviada"
        NEGOTIATION = "negociacion", "Negociación"
        WON = "ganada", "Ganada"
        LOST = "perdida", "Perdida"

    contact = models.ForeignKey(
        Contact,
        verbose_name="contacto",
        related_name="opportunities",
        on_delete=models.PROTECT,
    )
    title = models.CharField("título", max_length=140)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="responsable",
        related_name="opportunities",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    stage = models.CharField(
        "etapa",
        max_length=32,
        choices=Stage.choices,
        default=Stage.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "oportunidad"
        verbose_name_plural = "oportunidades"

    def __str__(self) -> str:
        return self.title


class OpportunityStageLog(models.Model):
    opportunity = models.ForeignKey(
        Opportunity,
        related_name="stage_logs",
        on_delete=models.CASCADE,
    )
    from_stage = models.CharField(max_length=32, blank=True)
    to_stage = models.CharField(max_length=32)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "cambio de etapa"
        verbose_name_plural = "cambios de etapa"


class ImportBatch(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    original_name = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "importación"
        verbose_name_plural = "importaciones"


class ImportRow(models.Model):
    class Action(models.TextChoices):
        SKIP = "omitir", "Omitir"
        CREATE = "crear", "Crear contacto nuevo"

    batch = models.ForeignKey(ImportBatch, related_name="rows", on_delete=models.CASCADE)
    line_number = models.PositiveIntegerField()
    payload = models.JSONField(default=dict)
    errors = models.JSONField(default=list)
    match_ids = models.JSONField(default=list)
    action = models.CharField(max_length=10, choices=Action.choices, default=Action.SKIP)

    class Meta:
        ordering = ["line_number"]

    @property
    def is_ambiguous(self) -> bool:
        return len(self.match_ids) > 1

    @property
    def is_duplicate(self) -> bool:
        return len(self.match_ids) == 1
