# Script: admin_routes.py
# Descripción: Orquestador principal de rutas administrativas.
# Uso: importado por la aplicación Flask.
# Requiere: Flask, MongoDB y módulos internos de administración.
# Variables de entorno: según configuración de la aplicación.
# Autor: EDF Developer - 2025-05-28

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, request
from flask_login import current_user  # type: ignore

from app.database import get_audit_logs_collection
from app.routes.admin.admin_api_status_routes import register_admin_api_status_routes
from app.routes.admin.admin_backup_routes import register_admin_backup_routes
from app.routes.admin.admin_catalog_routes import register_admin_catalog_routes
from app.routes.admin.admin_dashboard_routes import register_admin_dashboard_routes
from app.routes.admin.admin_db_routes import register_admin_db_routes
from app.routes.admin.admin_maintenance_routes import register_admin_maintenance_routes
from app.routes.admin.admin_notifications import register_admin_notification_routes
from app.routes.admin.admin_passwords import register_admin_password_routes
from app.routes.admin.admin_s3 import admin_s3_bp
from app.routes.admin.admin_system import admin_system_bp
from app.routes.admin.admin_tool_routes import register_admin_tool_routes
from app.routes.admin.admin_user_catalog_routes import register_admin_user_catalog_routes
from app.routes.admin.admin_user_routes import register_admin_user_routes
from app.routes.admin.admin_verify_users import register_admin_verify_user_routes


def log_action(
    action: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    collection: Optional[str] = None,
) -> None:
    """
    Registra una acción en el log de auditoría.

    Args:
        action (str): Nombre de la acción (ej: 'backup_created', 'user_updated')
        message (str): Mensaje descriptivo de la acción
        details (dict, optional): Detalles adicionales de la acción
        user_id (str, optional): ID del usuario que realizó la acción
        collection (str, optional): Nombre de la colección relacionada
    """
    try:
        # Obtener el ID de usuario actual si no se proporciona
        if not user_id and hasattr(current_user, "id"):
            user_id = str(current_user.id)

        # Crear el documento de log
        log_entry = {
            "action": action,
            "message": message,
            "details": details or {},
            "user_id": user_id,
            "collection": collection,
            "ip_address": request.remote_addr if request else None,
            "user_agent": request.headers.get("User-Agent") if request else None,
            "timestamp": datetime.utcnow(),
        }

        # Insertar en la colección de auditoría
        audit_logs = get_audit_logs_collection()
        if audit_logs is not None:
            audit_logs.insert_one(log_entry)

        # También registrar en el log de la aplicación
        current_app.logger.info(f"[AUDIT] {action}: {message}")

    except (AttributeError, TypeError, ValueError) as e:
        current_app.logger.error(
            f"Error al registrar en el log de auditoría: {str(e)}", exc_info=True
        )


logger = logging.getLogger(__name__)


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
register_admin_backup_routes(admin_bp)
register_admin_notification_routes(admin_bp)
register_admin_maintenance_routes(admin_bp)
register_admin_api_status_routes(admin_bp)
register_admin_db_routes(admin_bp)
register_admin_user_routes(admin_bp)
register_admin_user_catalog_routes(admin_bp)
register_admin_catalog_routes(admin_bp)
register_admin_tool_routes(admin_bp)
register_admin_dashboard_routes(admin_bp)
register_admin_verify_user_routes(admin_bp)
register_admin_password_routes(admin_bp)

# ...

# Función para registrar los blueprints
def register_admin_blueprints(app: Any) -> None:
    """
    Función para registrar blueprints adicionales de administración.
    Nota: admin_logs_bp ya está registrado en __init__.py
    """
    try:
        app.register_blueprint(admin_system_bp)
        app.register_blueprint(admin_s3_bp)
    except (AttributeError, ValueError, TypeError) as e:
        app.logger.error(f"Error en register_admin_blueprints: {str(e)}")
