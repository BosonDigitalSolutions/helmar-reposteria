from django import forms

from apps.core.forms import style_fields

from .models import Expense, Ingredient, Investment, StockMovement


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ("name", "unit", "reorder_level")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class MovementForm(forms.Form):
    kind = forms.ChoiceField(label="Tipo", choices=StockMovement.Kind.choices)
    quantity = forms.DecimalField(label="Cantidad", max_digits=12, decimal_places=3)
    unit_cost = forms.DecimalField(
        label="Costo por unidad",
        max_digits=12,
        decimal_places=4,
        required=False,
        help_text="Solo en una compra. Si el insumo está en gramos, el costo es por gramo.",
    )
    occurred_on = forms.DateField(label="Fecha", widget=forms.DateInput(attrs={"type": "date"}))
    note = forms.CharField(label="Nota", required=False, max_length=180)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ("category", "amount", "occurred_on", "note")
        widgets = {"occurred_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["note"].required = False
        style_fields(self)


class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ("name", "amount", "acquired_on", "note")
        widgets = {"acquired_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["note"].required = False
        style_fields(self)
