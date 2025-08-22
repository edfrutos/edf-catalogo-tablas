# Script: error_handlers.py
# Descripción: Manejadores de errores personalizados para la aplicación
# Uso: Importado automáticamente por Flask
# Requiere: Flask
# Variables de entorno: Ninguna
# Autor: EDF Developer - 2025-01-27

from flask import Blueprint, current_app, jsonify, request

errors_bp = Blueprint("errors", __name__)


@errors_bp.errorhandler(400)
def bad_request(error):
    """Maneja errores 400 (Bad Request) incluyendo requests malformados."""
    # Verificar si es un request malformado
    if hasattr(error, "description") and "Bad request version" in str(
        error.description
    ):
        current_app.logger.warning(f"Request malformado detectado: {error.description}")
        return (
            jsonify(
                {
                    "error": "Request malformado",
                    "message": "El navegador envió un request que el servidor no pudo entender",
                    "status": "error",
                }
            ),
            400,
        )

    # Para otros errores 400
    return (
        jsonify(
            {
                "error": "Bad Request",
                "message": (
                    str(error.description)
                    if hasattr(error, "description")
                    else "Request inválido"
                ),
                "status": "error",
            }
        ),
        400,
    )


@errors_bp.errorhandler(404)
def not_found(error):
    """Maneja errores 404 (Not Found)."""
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "La página o recurso solicitado no fue encontrado",
                "status": "error",
            }
        ),
        404,
    )


@errors_bp.errorhandler(413)
def request_entity_too_large(error):
    """Maneja errores 413 (Request Entity Too Large)."""
    current_app.logger.warning(f"Archivo demasiado grande: {error}")
    return (
        jsonify(
            {
                "error": "Request Entity Too Large",
                "message": "El archivo que intentas subir es demasiado grande. El límite máximo es 300MB.",
                "status": "error",
                "max_size": "300MB",
            }
        ),
        413,
    )


@errors_bp.errorhandler(500)
def internal_error(error):
    """Maneja errores 500 (Internal Server Error)."""
    current_app.logger.error(f"Error interno del servidor: {error}")
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "Ocurrió un error interno en el servidor",
                "status": "error",
            }
        ),
        500,
    )


@errors_bp.before_request
def log_request_info():
    """Registra información del request para debugging."""
    if request and hasattr(request, "headers"):
        current_app.logger.debug(f"Request: {request.method} {request.url}")
        current_app.logger.debug(
            f"Content-Type: {request.headers.get('Content-Type', 'No especificado')}"
        )
    else:
        current_app.logger.warning("Request malformado detectado en before_request")


@errors_bp.after_request
def log_response_info(response):
    """Registra información de la respuesta para debugging."""
    if response.status_code >= 400:
        current_app.logger.warning(f"Respuesta con error: {response.status_code}")
    return response
