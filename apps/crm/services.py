"""Detección de duplicados y lectura de CSV."""

import csv
import io

from django.db.models import Q

from .models import Contact, CrmSettings
from .normalization import digits, normalize_email

HEADER_MAP = {
    "nombre": "first_name",
    "apellidos": "last_name",
    "correo": "email",
    "telefono": "phone",
    "teléfono": "phone",
    "whatsapp": "whatsapp",
    "empresa": "company",
    "origen": "origin",
    "estado": "status",
    "etiquetas": "tags",
    "observaciones": "notes",
}

ORIGIN_ALIASES = {
    "whatsapp": Contact.Origin.WHATSAPP,
    "instagram": Contact.Origin.INSTAGRAM,
    "facebook": Contact.Origin.FACEBOOK,
    "referido": Contact.Origin.REFERRAL,
    "mostrador": Contact.Origin.COUNTER,
    "otro": Contact.Origin.OTHER,
}
STATUS_ALIASES = {
    "lead": Contact.Status.LEAD,
    "prospecto": Contact.Status.PROSPECT,
    "cliente": Contact.Status.CLIENT,
}
MAX_ROWS = 500


def find_matches(*, email="", phone="", whatsapp="", settings=None):
    rules = settings or CrmSettings.load()
    query = Q()
    normalized_email = normalize_email(email)
    phone_digits = digits(phone)
    whatsapp_digits = digits(whatsapp)
    if rules.match_email and normalized_email:
        query |= Q(normalized_email=normalized_email)
    if rules.match_phone and phone_digits:
        query |= Q(normalized_phone=phone_digits) | Q(normalized_whatsapp=phone_digits)
    if rules.match_phone and whatsapp_digits:
        query |= Q(normalized_phone=whatsapp_digits) | Q(normalized_whatsapp=whatsapp_digits)
    if not query:
        return []
    return list(Contact.objects.filter(query).distinct())


def parse_contact_csv(uploaded):
    raw = uploaded.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar en UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("El CSV no tiene encabezados.")
    mapped_headers = {}
    for header in reader.fieldnames:
        key = (header or "").strip().lower()
        if key in HEADER_MAP:
            mapped_headers[header] = HEADER_MAP[key]
    if "first_name" not in mapped_headers.values():
        raise ValueError("Falta la columna nombre.")
    rows = []
    for line_number, raw_row in enumerate(reader, start=2):
        if len(rows) >= MAX_ROWS:
            raise ValueError(f"El archivo supera {MAX_ROWS} contactos.")
        payload = {field: "" for field in HEADER_MAP.values()}
        for original, field in mapped_headers.items():
            payload[field] = (raw_row.get(original) or "").strip()
        rows.append((line_number, payload))
    if not rows:
        raise ValueError("El archivo no contiene contactos.")
    return rows


def validate_payload(payload):
    errors = []
    if not payload.get("first_name"):
        errors.append("Falta el nombre.")
    if not any(payload.get(field) for field in ("email", "phone", "whatsapp")):
        errors.append("Indica correo, teléfono o WhatsApp.")
    origin = payload.get("origin", "").strip().lower()
    if not origin:
        errors.append("Falta el origen.")
    elif origin not in ORIGIN_ALIASES:
        errors.append("El origen no es válido.")
    else:
        payload["origin"] = ORIGIN_ALIASES[origin]
    status = payload.get("status", "").strip().lower()
    if not status:
        payload["status"] = Contact.Status.LEAD
    elif status not in STATUS_ALIASES:
        errors.append("El estado comercial no es válido.")
    else:
        payload["status"] = STATUS_ALIASES[status]
    email = payload.get("email", "")
    if email and "@" not in email:
        errors.append("El correo no es válido.")
    return errors
