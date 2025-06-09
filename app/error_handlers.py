# app/error_handlers.py
from flask import Blueprint, render_template, request, jsonify
import logging

errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)

# Rutas que queremos ignorar (no registrar como errores 404)
IGNORED_PATHS = [
    '/.well-known/',
    '/favicon.ico',
    '/robots.txt',
    '/apple-touch-icon.png',
    '/sitemap.xml',
    '/ads.txt'
]

# -------------------------------------------
# Manejadores de errores personalizados
# -------------------------------------------

def should_ignore_404():
    """Determina si una ruta 404 debe ser ignorada."""
    path = request.path
    return any(ignored_path in path for ignored_path in IGNORED_PATHS)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Error 404: Página no encontrada"""
    if should_ignore_404():
        # Para rutas ignoradas, devolvemos una respuesta vacía con código 204 (No Content)
        return '', 204
        
    # Para rutas de API, devolvemos un JSON
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Recurso no encontrado',
            'code': 404
        }), 404
        
    # Para rutas normales, mostramos la página de error 404
    return render_template("not_found.html"), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Error 500: Error interno del servidor"""
    return render_template("error.html", error=str(error)), 500

@errors_bp.app_errorhandler(503)
def service_unavailable_error(error):
    """Error 503: Servicio no disponible"""
    return render_template("errors/503.html"), 503
