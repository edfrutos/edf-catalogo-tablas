"""
Middleware de Seguridad - EDF CatálogoDeTablas
==============================================

Implementa headers de seguridad y protecciones básicas
"""

from flask import request, abort, current_app
import re
from pathlib import Path


class SecurityMiddleware:
    """Middleware para implementar medidas de seguridad"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Inicializa el middleware con la aplicación Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # Registrar el middleware
        app.logger.info("🔒 Middleware de seguridad inicializado")

    def before_request(self):
        """Ejecutado antes de cada request"""
        # Protección contra path traversal
        if self._is_path_traversal_attempt(request.path):
            current_app.logger.warning(
                f"🚨 Intento de path traversal detectado: {request.path}"
            )
            abort(404)

        # Protección contra ataques de inyección básicos
        if self._is_suspicious_request(request):
            current_app.logger.warning(
                f"🚨 Request sospechoso detectado: {request.path}"
            )
            abort(400)

    def after_request(self, response):
        """Ejecutado después de cada request"""
        # Headers de seguridad (simplificados para desarrollo)
        response.headers["X-Content-Type-Options"] = "nosniff"
        # response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # response.headers["X-XSS-Protection"] = "1; mode=block"
        # response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # CSP deshabilitado para desarrollo local
        # response.headers["Content-Security-Policy"] = (
        #     "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://code.jquery.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self';"
        # )

        # Headers adicionales de seguridad
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response

    def _is_path_traversal_attempt(self, path):
        """Detecta intentos de path traversal"""
        # Permitir TODAS las rutas de archivos estáticos y recursos
        if path.startswith("/static/") or path.startswith("/static"):
            return False

        # Permitir favicon y otros recursos comunes
        if path in ["/favicon.ico", "/robots.txt", "/sitemap.xml"]:
            return False

        # Rutas permitidas (siempre seguras)
        safe_paths = [
            "/",
            "/static",
            "/login",
            "/register",
            "/logout",
            "/admin",
            "/dashboard",
            "/catalogs",
            "/maintenance",
            "/tools",
            "/api",
        ]

        # Si es una ruta segura conocida, permitir
        for safe_path in safe_paths:
            if path.startswith(safe_path):
                return False

        # Solo verificar patrones de path traversal reales y obvios
        suspicious_patterns = [
            r"\.\./",  # ../
            r"\.\.\\",  # ..\ (Windows)
            r"%2e%2e%2f",  # URL encoded ../
            r"%2e%2e%5c",  # URL encoded ..\ (Windows)
            r"%252e%252e",  # Double URL encoded ../
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True

        # Si no es obviamente malicioso, permitir
        return False

    def _is_suspicious_request(self, request):
        """Detecta requests sospechosos"""
        # Patrones de ataques comunes
        suspicious_patterns = [
            r"<script",  # XSS básico
            r"javascript:",  # JavaScript injection
            r"data:text/html",  # Data URI attacks
            r"vbscript:",  # VBScript injection
            r"onload=",  # Event handlers
            r"onerror=",  # Event handlers
            r"<iframe",  # Iframe injection
            r"<object",  # Object injection
            r"<embed",  # Embed injection
        ]

        # Verificar en URL y headers
        full_url = str(request.url)
        user_agent = request.headers.get("User-Agent", "")

        for pattern in suspicious_patterns:
            if re.search(pattern, full_url, re.IGNORECASE) or re.search(
                pattern, user_agent, re.IGNORECASE
            ):
                return True

        return False


# Instancia global del middleware
security_middleware = SecurityMiddleware()
