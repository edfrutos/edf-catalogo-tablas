# Script: filters.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 filters.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-07

from datetime import datetime


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


def init_app(app):
    """Register filters with the Flask app."""
    app.jinja_env.filters["datetimeformat"] = datetimeformat
