"""Utilidades para no escribir secretos en los logs."""

import re
from collections.abc import Mapping
from typing import Any

# Claves cuyo valor nunca debe aparecer en un log (contraseñas, tokens, claves, CSRF...)
_SECRET_KEY = re.compile(
    r"pass(word|wd)?|contrase|secret|token|api[_-]?key|csrf|credential|authorization",
    re.IGNORECASE,
)
REDACTED = "***"


def redact(data: Any) -> Any:
    """Copia de `data` con los valores sensibles sustituidos por '***'.

    Acepta mapeos (dict, ImmutableMultiDict de Flask, anidados), listas y escalares.
    """
    if isinstance(data, Mapping):
        return {
            k: (REDACTED if _SECRET_KEY.search(str(k)) else redact(v))
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [redact(v) for v in data]
    return data
