from django import forms

from apps.core.forms import style_fields

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("kind", "method", "amount", "paid_on", "note")
        widgets = {"paid_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["note"].required = False
        style_fields(self)
