"""Normalización de correo y teléfono para detectar duplicados."""


def digits(value: str) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()
