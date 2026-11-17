"""Filtros de logging que evitan guardar secretos."""

import logging


class RedactSecretsFilter(logging.Filter):
    """Sustituye mensajes que podrían incluir contraseñas o tokens."""

    _markers = ("password", "secret", "token", "authorization", "contraseña")

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage().lower()
        except Exception:
            return True
        if any(marker in message for marker in self._markers):
            record.msg = "Mensaje omitido para no registrar secretos."
            record.args = ()
        return True
