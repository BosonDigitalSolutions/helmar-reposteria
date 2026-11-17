"""Pruebas. Reutiliza SQLite de desarrollo con un hasher rápido."""

import tempfile
from pathlib import Path

from .development import *  # noqa: F403

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="helymar-test-media-"))
