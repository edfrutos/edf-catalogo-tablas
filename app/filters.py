# Script: filters.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 filters.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-07

from datetime import datetime

from app.utils.row_media import display_name, media_key


def datetimeformat(value, format="%Y-%m-%d %H:%M"):
    """Format a datetime object or timestamp string."""
    if value is None:
        return ""
    if isinstance(value, str):
        # Try to parse the string as a datetime
        try:
            # Try ISO format
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try parsing as timestamp
                value = datetime.fromtimestamp(float(value))
            except (ValueError, TypeError):
                return ""
    elif not isinstance(value, datetime):
        # If it's not a datetime and not a string, try to convert to datetime
        try:
            value = datetime.fromtimestamp(float(value))
        except (ValueError, TypeError):
            return ""

    return value.strftime(format)


def media_url(value):
    """URL servible de un archivo guardado (documento o multimedia).

    Enlaces externos y rutas ya resueltas se devuelven tal cual; los nombres
    sueltos y los enlaces de nuestro bucket pasan por el proxy /admin/s3/, que
    sirve desde S3 y, si no está, desde disco.
    """
    value = (value or "").strip() if isinstance(value, str) else ""
    if not value:
        return ""
    if value.startswith("http") and ".amazonaws.com/" not in value:
        return value
    if value.startswith("/") and not value.startswith("/admin/s3/"):
        return value
    return "/admin/s3/" + media_key(value)


def init_app(app):
    """Register filters with the Flask app."""
    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["media_url"] = media_url
    app.jinja_env.filters["media_name"] = display_name
