from django.forms import inlineformset_factory
from django import forms

from apps.core.forms import style_fields

from .models import Product, ProductCustomization, ProductImage, ProductPresentation
from .validation import validate_uploaded_image


class ProductForm(forms.ModelForm):
    new_image = forms.ImageField(label="Fotografía", required=False)

    class Meta:
        model = Product
        fields = (
            "name",
            "sku",
            "category",
            "description",
            "price_mode",
            "base_price",
            "is_active",
            "is_customizable",
            "lead_time_days",
            "display_order",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_sku(self):
        return self.cleaned_data["sku"].strip().upper()

    def clean_new_image(self):
        image = self.cleaned_data.get("new_image")
        if image:
            validate_uploaded_image(image)
        return image


class PresentationForm(forms.ModelForm):
    class Meta:
        model = ProductPresentation
        fields = ("name", "display_order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["display_order"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get("name") or "").strip():
            cleaned["DELETE"] = True
        return cleaned


class CustomizationForm(forms.ModelForm):
    class Meta:
        model = ProductCustomization
        fields = ("name", "display_order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["display_order"].required = False
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get("name") or "").strip():
            cleaned["DELETE"] = True
        return cleaned


PresentationFormSet = inlineformset_factory(
    Product,
    ProductPresentation,
    form=PresentationForm,
    extra=1,
    can_delete=True,
)
CustomizationFormSet = inlineformset_factory(
    Product,
    ProductCustomization,
    form=CustomizationForm,
    extra=1,
    can_delete=True,
)


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ("image", "alt_text", "display_order")

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            validate_uploaded_image(image)
        return image
