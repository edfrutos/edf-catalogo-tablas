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


@admin_bp.route("/")
@admin_required
def dashboard_admin():
    db = get_mongo_db()
    if db is None:
        flash(
            "No se pudo acceder a la base de datos. Contacte con el administrador.",
            "error",
        )
        return render_template(
            "error.html",
            mensaje="No se pudo conectar a la base de datos. Contacte con el administrador.",
        )
    # Intentar obtener la colección de usuarios de diferentes formas
    users_collection = getattr(current_app, "users_collection", None)
    if users_collection is None:
        # Intentar obtener desde g
        from flask import g

        users_collection = getattr(g, "users_collection", None)
        if users_collection is None:
            # Como último recurso, obtener directamente de la base de datos
            try:
                users_collection = db["users"]
            except Exception:
                users_collection = None
    if users_collection is None:
        flash("No se pudo acceder a la colección de usuarios.", "error")
        return render_template(
            "error.html", mensaje="No se pudo conectar a la colección de usuarios."
        )
    try:
        search = request.args.get("search", "").strip()
        search_type = request.args.get("search_type", "name")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)

        # Limitar per_page a valores razonables
        per_page = max(10, min(100, per_page))

        usuarios = list(users_collection.find())
        total_usuarios = len(usuarios)
        try:
            tablas = list(db["spreadsheets"].find().sort("created_at", -1))
        except (KeyError, AttributeError, TypeError) as e:
            print(f"[ERROR][ADMIN] Consulta a spreadsheets falló: {e}")
            tablas = []
        try:
            catalogos = list(db["catalogs"].find().sort("created_at", -1))
        except (KeyError, AttributeError, TypeError) as e:
            print(f"[ERROR][ADMIN] Consulta a catalogs falló: {e}")
            catalogos = []
        for t in tablas:
            t["tipo"] = "spreadsheet"
            normalize_catalog_rows(t)
        for c in catalogos:
            c["tipo"] = "catalog"
            normalize_catalog_rows(c)
        registros = tablas + catalogos
        catalogos_por_usuario = {}
        for usuario in usuarios:
            catalogos_por_usuario[str(usuario["_id"])] = {
                "email": usuario.get("email", "Sin email"),
                "nombre": usuario.get("name", usuario.get("username", "Sin nombre")),
                "username": usuario.get("username", "Sin usuario"),
                "role": usuario.get("role", "user"),
                "count": 0,
                "last_update": None,
            }
        for reg in registros:
            owner = reg.get("owner") or reg.get("created_by") or reg.get("owner_name")
            for user_id, user_info in catalogos_por_usuario.items():
                if user_info["username"] == owner or user_info["email"] == owner:
                    catalogos_por_usuario[user_id]["count"] += 1
                    if "updated_at" in reg and reg["updated_at"]:
                        last_update = reg["updated_at"]
                        if isinstance(last_update, str):
                            try:
                                last_update = datetime.strptime(
                                    last_update, "%Y-%m-%d %H:%M:%S"
                                )
                            except (ValueError, TypeError):
                                try:
                                    last_update = datetime.strptime(
                                        last_update, "%Y-%m-%d %H:%M"
                                    )
                                except (ValueError, TypeError):
                                    last_update = None
                        if last_update and (
                            catalogos_por_usuario[user_id]["last_update"] is None
                            or last_update
                            > catalogos_por_usuario[user_id]["last_update"]
                        ):
                            catalogos_por_usuario[user_id]["last_update"] = last_update
        usuarios_con_catalogos = []
        for _user_id, user_info in catalogos_por_usuario.items():
            usuarios_con_catalogos.append(user_info)

        # Filtrar registros por usuario si es necesario
        mis_registros = []
        if search:
            if search_type == "owner":
                mis_registros = [
                    r
                    for r in registros
                    if search.lower()
                    in (
                        r.get("owner", "")
                        or r.get("created_by", "")
                        or r.get("owner_name", "")
                    ).lower()
                ]
            else:
                mis_registros = [
                    r for r in registros if search.lower() in r.get("name", "").lower()
                ]
        else:
            mis_registros = registros

        # Aplicar paginación
        total_catalogos = len(mis_registros)
        total_pages = (total_catalogos + per_page - 1) // per_page
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        mis_registros_paginados = mis_registros[start_idx:end_idx]

        porcentaje = (total_catalogos / total_usuarios * 100) if total_usuarios else 0

        return render_template(
            "admin/dashboard_admin.html",
            total_usuarios=total_usuarios,
            total_catalogos=total_catalogos,
            porcentaje=porcentaje,
            mis_registros=mis_registros_paginados,
            search=search,
            search_type=search_type,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_prev=page > 1,
            has_next=page < total_pages,
            prev_page=page - 1,
            next_page=page + 1,
        )
    except Exception as e:
        print(f"[ERROR][ADMIN] Error en dashboard_admin: {e}")
        flash(f"Error al cargar el dashboard: {e}", "error")
        return render_template(
            "error.html", mensaje=f"Error al cargar el dashboard: {e}"
        )


# Ruta adicional para compatibilidad con /admin/dashboard
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Ruta de compatibilidad para /admin/dashboard - redirige al dashboard de mantenimiento"""
    return redirect(url_for("maintenance.maintenance_dashboard"))


# Removed duplicate maintenance route - using dedicated maintenance blueprint instead


@admin_bp.route("/system-status")
@admin_required
def system_status():
    try:
        # Obtener datos del sistema
        data = get_system_status_data()
        # Obtener la lista de archivos de log
        logs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../logs")
        )
        log_files = get_log_files(logs_dir)
        # Obtener la lista de archivos de backup
        backup_dir = os.path.abspath(os.path.join(os.getcwd(), "backups"))
        backup_files = get_backup_files(backup_dir)
        # Pasar cache_stats y temp_files como variables independientes para el template
        cache_stats = data.get("cache_stats", {})
        temp_files = data.get(
            "temp_files", {"count": 0, "total_size_mb": 0, "files": []}
        )

        # Asegurar que data.health.metrics tenga la estructura correcta
        if "health" not in data:
            data["health"] = {"metrics": {}}
        if "metrics" not in data["health"]:
            data["health"]["metrics"] = {}
        if "temp_files" not in data["health"]["metrics"]:
            data["health"]["metrics"]["temp_files"] = temp_files

        return render_template(
            "admin/system_status.html",
            data=data,
            log_files=log_files,
            backup_files=backup_files,
            cache_stats=cache_stats,
            temp_files=temp_files,
        )
    except Exception as e:
        logger.error(f"Error en system_status: {str(e)}", exc_info=True)
        flash("Error al obtener el estado del sistema", "danger")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route("/system-status/report")
@admin_required
def system_status_report():
    data = get_system_status_data(full=True)
    response = current_app.response_class(
        response=json.dumps(data, indent=2, default=str), mimetype="application/json"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=system_status_report.json"
    )
    return response


def get_system_status_data(full: bool = False) -> Dict[str, Any]:
    try:
        # Obtener informe completo de estado (NO recalcular nada costoso aquí)
        health_report = monitoring.get_health_status()
        # Obtener estadísticas de solicitudes
        request_stats = monitoring._app_metrics["request_stats"]
        # Calcular uptime
        start_time_str = monitoring._app_metrics["start_time"]
        # Asegurar que start_time sea un string
        if isinstance(start_time_str, (list, tuple)):
            start_time_str = (
                start_time_str[0]
                if start_time_str
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        elif not isinstance(start_time_str, str):
            start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split(".")[0]  # Formato HH:MM:SS
        # Obtener métricas de memoria
        process = psutil.Process(os.getpid())  # type: ignore
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        system_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()  # type: ignore
        # Top 5 procesos por consumo de memoria
        all_procs = [
            p
            for p in psutil.process_iter(  # type: ignore
                ["pid", "name", "memory_info", "memory_percent"]
            )
            if p.info.get("memory_percent") is not None
        ]
        top_procs = sorted(
            all_procs, key=lambda p: p.info["memory_percent"], reverse=True
        )[:5]
        top_processes = [
            {
                "pid": p.info["pid"],
                "name": p.info["name"],
                "rss_mb": (
                    round(p.info["memory_info"].rss / 1024 / 1024, 2)
                    if p.info["memory_info"]
                    else None
                ),
                "mem_percent": round(p.info["memory_percent"], 2),
            }
            for p in top_procs
        ]
        # Info de plataforma
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        mem_breakdown = {
            "python_process": {
                "pid": process.pid,
                "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
                "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
                "percent": round(mem_percent, 2),
            },
            "system": {
                "total_mb": round(system_mem.total / 1024 / 1024, 2),
                "used_mb": round(system_mem.used / 1024 / 1024, 2),
                "percent": system_mem.percent,
            },
            "swap": {
                "total_mb": round(swap_mem.total / 1024 / 1024, 2),
                "used_mb": round(swap_mem.used / 1024 / 1024, 2),
                "percent": swap_mem.percent,
            },
            "top_processes": top_processes,
            "platform": platform_info,
        }
        temp_files_list = list_temp_files()

        # Asegurar que health_report.metrics.temp_files tenga la estructura correcta
        if "metrics" in health_report and "temp_files" in health_report["metrics"]:
            temp_files_metrics = health_report["metrics"]["temp_files"]
            # Asegurar que temp_files tenga la estructura esperada por el template
            if not isinstance(temp_files_metrics, dict):
                health_report["metrics"]["temp_files"] = {
                    "count": 0,
                    "total_size_mb": 0,
                    "files": [],
                }
            elif "count" not in temp_files_metrics:
                health_report["metrics"]["temp_files"]["count"] = len(
                    temp_files_metrics.get("files", [])
                )

        status_data = {
            "health": health_report,
            "uptime": uptime_str,
            "request_stats": request_stats,
            "database": monitoring._app_metrics["database_status"],
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory": mem_breakdown,
            "cache_stats": get_cache_stats(),
            "temp_files": temp_files_list,
        }
        if full:
            status_data["raw_psutil"] = {
                "process": dict(mem_info._asdict()),
                "system": dict(system_mem._asdict()),
                "swap": dict(swap_mem._asdict()),
            }
        return status_data
    except (AttributeError, KeyError, OSError, ImportError) as e:
        logger.error(f"Error en get_system_status_data: {str(e)}", exc_info=True)
        # Estructura de error más completa y consistente
        error_health = {
            "status": "error",
            "metrics": {
                "system_status": {
                    "cpu_usage": 0,
                    "memory_usage": {"used_mb": 0, "total_mb": 0, "percent": 0},
                    "disk_usage": {"used_gb": 0, "total_gb": 0, "percent": 0},
                },
                "temp_files": {"count": 0, "total_size_mb": 0, "files": []},
            },
        }
        return {
            "health": error_health,
            "uptime": "Error",
            "request_stats": {"total_requests": 0},
            "database": {"is_available": False, "response_time_ms": 0},
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory": {},
            "temp_files": [],
        }


# ...

# Función para registrar los blueprints
def register_admin_blueprints(app: Any) -> None:
    """
    Función para registrar blueprints adicionales de administración.
    Nota: admin_logs_bp ya istrado en __init__.py
    """
    try:
        app.register_blueprint(admin_system_bp)
        app.register_blueprint(admin_s3_bp)
    except (AttributeError, ValueError, TypeError) as e:
        app.logger.error(f"Error en register_admin_blueprints: {str(e)}")
