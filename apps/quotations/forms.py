from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.catalog.models import Product
from apps.core.forms import style_fields
from apps.core.lines import clean_line
from apps.crm.models import Contact, Opportunity

from .models import Quote, QuoteLine


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = (
            "contact",
            "opportunity",
            "event_date",
            "event_time",
            "valid_until",
            "delivery_type",
            "address",
            "discount",
            "notes",
        )
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "event_time": forms.TimeInput(attrs={"type": "time"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = Contact.objects.order_by("first_name", "last_name")
        self.fields["opportunity"].required = False
        self.fields["opportunity"].queryset = Opportunity.objects.select_related("contact").order_by(
            "-updated_at"
        )
        self.fields["opportunity"].label_from_instance = (
            lambda item: f"{item.title} · {item.contact.full_name}"
        )
        self.fields["valid_until"].required = False
        self.fields["address"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        contact = cleaned.get("contact")
        opportunity = cleaned.get("opportunity")
        if opportunity and contact and opportunity.contact_id != contact.pk:
            self.add_error("opportunity", "La oportunidad pertenece a otro contacto.")
        if cleaned.get("delivery_type") == Quote.Delivery.SHIP and not (cleaned.get("address") or "").strip():
            self.add_error("address", "Indica la dirección de envío.")
        return cleaned


class QuoteLineForm(forms.ModelForm):
    class Meta:
        model = QuoteLine
        fields = ("description", "product", "quantity", "unit_price")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["product"].required = False
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
        self.fields["quantity"].required = False
        self.fields["unit_price"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        return clean_line(cleaned)


class BaseQuoteLineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            if "DELETE" in form.fields:
                form.fields["DELETE"].label = "Quitar partida"

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        active = [
            form
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get("description")
        ]
        if not active:
            raise forms.ValidationError("Agrega al menos una partida.")


QuoteLineFormSet = inlineformset_factory(
    Quote,
    QuoteLine,
    form=QuoteLineForm,
    formset=BaseQuoteLineFormSet,
    extra=1,
    can_delete=True,
)
