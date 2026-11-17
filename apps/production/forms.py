from django import forms

from apps.core.forms import style_fields

from .models import ProductionJob


class ProductionJobForm(forms.ModelForm):
    class Meta:
        model = ProductionJob
        fields = ("scheduled_date", "status", "decoration", "dedication", "warnings", "notes")
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "warnings": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
