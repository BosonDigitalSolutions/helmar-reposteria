"""Datos de marca disponibles en las plantillas."""

import re

from django.conf import settings

_WHATSAPP = re.compile(r"^\d{10,15}$")


def helymar(request):
    from apps.accounts.views import StaffAuthenticationForm

    raw = settings.HELYMAR_WHATSAPP_NUMBER or ""
    number = raw if _WHATSAPP.fullmatch(raw) else ""
    login_form = None
    if not request.user.is_authenticated:
        login_form = StaffAuthenticationForm(request)
        login_form.fields["username"].widget.attrs.pop("autofocus", None)
    return {
        "helymar_whatsapp_number": number,
        "helymar_whatsapp_ready": bool(number),
        "login_form": login_form,
    }
