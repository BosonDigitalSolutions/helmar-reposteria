"""Folios COT-AAAA-0001 y PED-AAAA-0001, sin huecos bajo concurrencia."""

from django.db import transaction
from django.utils import timezone

from apps.core.models import FolioSequence


def next_folio(prefix: str) -> str:
    year = timezone.localdate().year
    with transaction.atomic():
        try:
            sequence = FolioSequence.objects.select_for_update().get(prefix=prefix, year=year)
        except FolioSequence.DoesNotExist:
            sequence = FolioSequence.objects.create(prefix=prefix, year=year, last_number=0)
            sequence = FolioSequence.objects.select_for_update().get(pk=sequence.pk)
        sequence.last_number += 1
        sequence.save(update_fields=["last_number"])
    return f"{prefix}-{year}-{sequence.last_number:04d}"
