"""Entorno local. La base de datos de localhost es SQLite."""

from .base import *  # noqa: F403
from .base import BASE_DIR, env

DEBUG = True
SECRET_KEY = env(
    "SECRET_KEY",
    default="dev-only-helymar-no-usar-en-produccion",
)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if not HELYMAR_WHATSAPP_NUMBER:
    HELYMAR_WHATSAPP_NUMBER = "5638773661"
