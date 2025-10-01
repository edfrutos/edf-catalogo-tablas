# app/routes/error_routes.py

import logging

from flask import Blueprint, current_app, render_template  # noqa: F401

logger = logging.getLogger(__name__)
errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def page_not_found(e):
    # Solo registrar 404s que no sean recursos estáticos comunes
    from flask import request

    path = request.path

    # Filtrar recursos estáticos comunes que generan ruido
    static_extensions = (
        ".css",
        ".js",
        ".ico",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".woff",
        ".woff2",
        ".ttf",
        ".map",
    )
    common_paths = ("/favicon.ico", "/robots.txt", "/sitemap.xml", "/apple-touch-icon")

    if not (
        path.endswith(static_extensions) or path in common_paths or "/static/" in path
    ):
        logger.warning(f"Error 404: Página no encontrada - {path}")

    return render_template("error/404.html"), 404


@errors_bp.app_errorhandler(500)
def server_error(e):
    logger.error(f"Error 500: Error interno del servidor - {e}")
    return render_template("error/500.html"), 500


@errors_bp.app_errorhandler(403)
def forbidden(e):
    logger.warning(f"Error 403: Acceso prohibido - {e}")
    return render_template("error/403.html"), 403


@errors_bp.app_errorhandler(401)
def unauthorized(e):
    logger.warning(f"Error 401: No autorizado - {e}")
    return render_template("error/401.html"), 401
