"""Validación de imágenes del catálogo."""

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 2 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_uploaded_image(uploaded) -> None:
    if uploaded.size > MAX_IMAGE_BYTES:
        raise ValidationError("La imagen no puede superar 2 MB.")
    try:
        image = Image.open(uploaded)
        image.verify()
        detected = image.format
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
    finally:
        uploaded.seek(0)
    if detected not in ALLOWED_FORMATS:
        raise ValidationError("Usa una imagen JPG, PNG o WEBP.")
