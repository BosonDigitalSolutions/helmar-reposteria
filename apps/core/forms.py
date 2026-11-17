"""Estilos compartidos de los formularios del panel."""

CONTROL = "w-full rounded-xl border border-chocolate/15 bg-white px-3 py-2 text-ink"


def style_fields(form) -> None:
    for field in form.fields.values():
        widget = field.widget
        if getattr(widget, "input_type", "") == "checkbox":
            widget.attrs.setdefault("class", "h-4 w-4 accent-cherry")
        elif getattr(widget, "input_type", "") == "file":
            widget.attrs.setdefault("class", "block w-full text-sm")
        else:
            widget.attrs.setdefault("class", CONTROL)
