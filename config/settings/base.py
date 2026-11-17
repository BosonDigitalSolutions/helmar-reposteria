"""Configuración compartida. El motor de base de datos lo define cada entorno."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    env.read_env(_env_file)

SECRET_KEY = env("SECRET_KEY", default="")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "axes",
    "apps.core",
    "apps.accounts",
    "apps.dashboard",
    "apps.catalog",
    "apps.crm",
    "apps.quotations",
    "apps.orders",
    "apps.payments",
    "apps.production",
    "apps.inventory",
    "apps.notifications",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.helymar",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:landing"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

STORAGES = {
    "default": {
        "BACKEND": env(
            "FILE_STORAGE_BACKEND",
            default="django.core.files.storage.FileSystemStorage",
        )
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

HELYMAR_WHATSAPP_NUMBER = env("HELYMAR_WHATSAPP_NUMBER", default="")

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "redact_secrets": {
            "()": "config.log_filters.RedactSecretsFilter",
        },
    },
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "filters": ["redact_secrets"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "axes": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
