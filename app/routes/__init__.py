# app/routes/__init__.py
# Importar los blueprints de diagnóstico directamente
# from app.routes.debug_routes import debug_bp  # Archivo no existe
from app.routes.admin_diagnostic import admin_diagnostic_bp
from app.routes.admin_routes import admin_bp
from app.routes.auth_routes import auth_bp
from app.routes.catalog_images_routes import image_bp
from app.routes.catalogs_routes import catalogs_bp
from app.routes.dev_template import bp_dev_template
from app.routes.diagnostico import diagnostico_bp
from app.routes.emergency_access import emergency_bp
from app.routes.error_routes import errors_bp
from app.routes.main_routes import main_bp
from app.routes.usuarios_routes import usuarios_bp

# Exportar los blueprints para que sean accesibles al importar desde app.routes
__all__ = [
    "main_bp",
    "auth_bp",
    "catalogs_bp",
    "image_bp",
    "usuarios_bp",
    "admin_bp",
    "errors_bp",
    "emergency_bp",
    # "debug_bp",  # Archivo no existe
    "admin_diagnostic_bp",
    "diagnostico_bp",
    "bp_dev_template",
]
