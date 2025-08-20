# Script: clean_logging.py
# Descripción: [Configuración para limpiar el logging excesivo de la aplicación. Aplica configuraciones para reducir la información verbosa que ya no es necesaria.]
# Uso: python3 clean_logging.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Configuración para limpiar el logging excesivo de la aplicación.
Aplica configuraciones para reducir la información verbosa que ya no es necesaria.
"""

import logging

from flask import Flask


def setup_clean_logging():
    """
    Configura logging limpio para producción/uso estable.
    Elimina toda la información de debugging y seguimiento excesivo.
    """

    # Configurar nivel base más restrictivo
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,  # Fuerza la reconfiguración
    )

    # Silenciar completamente los logs de pymongo (conexiones, heartbeat, etc.)
    logging.getLogger("pymongo").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.topology").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.connection").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.command").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.CRITICAL)

    # Silenciar otros sistemas verbosos
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)
    logging.getLogger("botocore").setLevel(logging.CRITICAL)
    logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
    logging.getLogger("requests").setLevel(logging.CRITICAL)

    # Configurar logger de la aplicación para mostrar solo errores importantes
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.ERROR)

    # Configurar flask para mostrar solo errores
    logging.getLogger("flask").setLevel(logging.ERROR)

    print("✅ Logging limpiado - Solo se mostrarán errores importantes")


def apply_to_flask_app(app: Flask):
    """Aplica la configuración de logging limpio a una aplicación Flask"""

    # Configurar el logger de la aplicación Flask
    app.logger.setLevel(logging.ERROR)

    # Eliminar handlers verbosos si existen
    for handler in app.logger.handlers[:]:
        if handler.level < logging.ERROR:
            app.logger.removeHandler(handler)

    # Configurar también en modo desarrollo
    if app.config.get("DEBUG"):
        app.logger.setLevel(logging.WARNING)
