# Script: admin_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from app.routes.admin.admin_system import admin_system_bp
from app.routes.admin.admin_s3 import admin_s3_bp
from app.routes.admin.admin_logs import get_log_files
from app.routes.admin.admin_backup_utils import get_backup_dir, get_backup_files
from app.routes.admin.admin_backup_routes import register_admin_backup_routes
from app.routes.admin.admin_notifications import register_admin_notification_routes
from app.routes.admin.admin_maintenance_routes import register_admin_maintenance_routes
from app.routes.admin.admin_api_status_routes import register_admin_api_status_routes
from app.routes.admin.admin_db_routes import register_admin_db_routes
from app.routes.admin.admin_verify_users import register_admin_verify_user_routes
from app.routes.admin.admin_user_routes import register_admin_user_routes
from app.routes.admin.admin_user_catalog_routes import register_admin_user_catalog_routes
from app.routes.admin.admin_catalog_routes import register_admin_catalog_routes
from app.routes.admin.admin_tool_routes import register_admin_tool_routes
from app.routes.admin.admin_dashboard_routes import register_admin_dashboard_routes
from app.routes.admin.admin_backup_restore_utils import (
    BackupRestoreError,
    is_mongodb_binary_dump_name,
    prepare_restore_documents,
    read_backup_json_file,
)
from app.routes.admin.admin_passwords import register_admin_password_routes
import csv
import io
import json
import logging
import os
import platform
import re
import shutil
import tempfile
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
import requests  # pyright: ignore[reportDuplicateImport]
from bson import ObjectId
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user  # type: ignore
from werkzeug.security import generate_password_hash

import app.monitoring as monitoring
import app.notifications as notifications
from app.audit import audit_log
from app.cache_system import clear_cache, get_cache_stats
from app.utils.catalog_utils import get_catalog_rows, normalize_catalog_rows
from app.database import (
    get_audit_logs_collection,
    get_catalogs_collection,
    get_mongo_client,
    get_mongo_db,
    get_reset_tokens_collection,
    get_users_collection,
)
from app.decorators import admin_required
from app.decorators import admin_required as admin_required_logs
from app.decorators import login_required
from app.routes.s3_utils import get_s3_url
from app.routes.temp_files_utils import delete_temp_files, list_temp_files
from tools.db_utils.google_drive_utils import list_files_in_folder, upload_to_drive


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
