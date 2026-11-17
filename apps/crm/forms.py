from django import forms
from django.contrib.auth import get_user_model

from apps.core.forms import style_fields

from .models import Activity, Contact, CrmSettings, Note, Opportunity

User = get_user_model()


def commercial_users():
    return User.objects.filter(
        is_active=True,
        role__in=[User.Role.ADMINISTRADOR, User.Role.VENTAS],
    ).order_by("first_name", "username")


class ContactForm(forms.ModelForm):
    tags_text = forms.CharField(
        label="Etiquetas",
        required=False,
        help_text="Separadas por comas.",
    )

    class Meta:
        model = Contact
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "whatsapp",
            "company",
            "origin",
            "status",
            "observations",
            "owner",
            "next_follow_up",
        )
        widgets = {"next_follow_up": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = commercial_users()
        self.fields["owner"].required = False
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(
                self.instance.tags.order_by("name").values_list("name", flat=True)
            )
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if not any(cleaned.get(field) for field in ("email", "phone", "whatsapp")):
            self.add_error("email", "Indica correo, teléfono o WhatsApp.")
        return cleaned

    def save(self, commit=True):
        contact = super().save(commit=commit)
        if commit:
            self.save_tags(contact)
        return contact

    def save_tags(self, contact):
        from .models import Tag

        names = []
        for part in self.cleaned_data.get("tags_text", "").split(","):
            name = part.strip()
            if name and name not in names:
                names.append(name)
        tags = [Tag.objects.get_or_create(name=name)[0] for name in names]
        contact.tags.set(tags)


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ("body",)
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ("summary",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ("title", "contact", "owner", "stage")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = Contact.objects.order_by("first_name", "last_name")
        self.fields["owner"].queryset = commercial_users()
        self.fields["owner"].required = False
        style_fields(self)


class CrmSettingsForm(forms.ModelForm):
    class Meta:
        model = CrmSettings
        fields = ("match_email", "match_phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class ImportUploadForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo CSV",
        help_text="Columnas: nombre, apellidos, correo, telefono, whatsapp, empresa, origen, estado, etiquetas, observaciones.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_archivo(self):
        uploaded = self.cleaned_data["archivo"]
        if uploaded.size > 1_000_000:
            raise forms.ValidationError("El archivo supera 1 MB.")
        if not uploaded.name.lower().endswith(".csv"):
            raise forms.ValidationError("Sube un archivo CSV.")
        return uploaded
