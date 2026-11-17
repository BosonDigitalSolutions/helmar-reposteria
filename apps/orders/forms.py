from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.catalog.models import Product
from apps.core.forms import CONTROL, style_fields
from apps.core.lines import clean_line
from apps.crm.models import Contact
from apps.quotations.models import Quote

from .models import Order, OrderLine


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("contact", "event_at", "delivery_type", "address", "discount", "notes")
        widgets = {
            "event_at": forms.SplitDateTimeWidget(
                date_attrs={"type": "date", "class": CONTROL},
                time_attrs={"type": "time", "class": CONTROL},
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = Contact.objects.order_by("first_name", "last_name")
        self.fields["address"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("delivery_type") == Quote.Delivery.SHIP and not (cleaned.get("address") or "").strip():
            self.add_error("address", "Indica la dirección de envío.")
        return cleaned


class OrderHeaderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("event_at", "delivery_type", "address", "notes")
        widgets = {
            "event_at": forms.SplitDateTimeWidget(
                date_attrs={"type": "date", "class": CONTROL},
                time_attrs={"type": "time", "class": CONTROL},
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("delivery_type") == Quote.Delivery.SHIP and not (cleaned.get("address") or "").strip():
            self.add_error("address", "Indica la dirección de envío.")
        return cleaned


class OrderLineForm(forms.ModelForm):
    class Meta:
        model = OrderLine
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


class BaseOrderLineFormSet(BaseInlineFormSet):
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


OrderLineFormSet = inlineformset_factory(
    Order,
    OrderLine,
    form=OrderLineForm,
    formset=BaseOrderLineFormSet,
    extra=1,
    can_delete=True,
)
