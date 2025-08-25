# Script: admin_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import csv
import io
import json
import logging
import os
import platform
import re
import shutil
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil  # type: ignore
import requests
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
from app.cache_system import get_cache_stats
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


# @admin_bp.route("/scripts-tools")
# def scripts_tools_overview():
#     # Esta ruta está comentada para evitar conflictos con scripts_bp
#     # La funcionalidad de scripts y herramientas ahora está en /admin/tools/
#     pass


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
            t["data"] = t.get("data", [])
        for c in catalogos:
            c["tipo"] = "catalog"
            c["data"] = c.get("rows", [])
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
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        system_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        # Top 5 procesos por consumo de memoria
        all_procs = [
            p
            for p in psutil.process_iter(
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


@admin_bp.route("/logs/list")
@admin_required
def logs_list():
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_files = get_log_files(logs_dir)
    return jsonify({"status": "success", "files": [f["name"] for f in log_files]})


def get_log_files(logs_dir: str) -> List[Dict[str, Any]]:
    """Obtiene la lista de archivos de log disponibles (máx 20 más recientes)"""
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            return []
        log_files = []
        for file in os.listdir(logs_dir):
            if file.endswith(".log"):
                file_path = os.path.join(logs_dir, file)
                stats = os.stat(file_path)
                size_kb = stats.st_size / 1024
                mod_time = datetime.fromtimestamp(stats.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                log_files.append(
                    {"name": file, "size": f"{size_kb:.2f} KB", "modified": mod_time}
                )
        # Ordenar y limitar a 20 más recientes
        log_files.sort(key=lambda x: x["modified"], reverse=True)
        return log_files[:20]
    except (OSError, PermissionError) as e:
        logger.error(f"Error al obtener archivos de log: {str(e)}", exc_info=True)
        return []


def get_backup_files(backup_dir: str) -> List[Dict[str, Any]]:
    """Obtiene la lista de archivos de backup disponibles (máx 20 más recientes, sin recursividad)"""
    try:
        logger.info(f"Buscando archivos de backup en: {backup_dir}")
        if not os.path.exists(backup_dir):
            logger.warning(f"El directorio de backups no existe: {backup_dir}")
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"Directorio de backups creado: {backup_dir}")
            return []
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith("."):
                continue
            full_path = os.path.join(backup_dir, file)
            if not os.path.isfile(full_path):
                continue
            # Solo archivos de backup por extensión
            if not any(
                file.endswith(ext)
                for ext in [
                    ".bak",
                    ".backup",
                    ".zip",
                    ".tar",
                    ".gz",
                    ".json.gz",  # Agregar extensión específica para backups comprimidos
                    ".sql",
                    ".dump",
                    ".old",
                    ".back",
                    ".tmp",
                    ".swp",
                    "~",
                    ".csv",
                    ".json",
                ]
            ):
                continue
            stats = os.stat(full_path)
            size_bytes = stats.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            mod_time = datetime.fromtimestamp(stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            backup_files.append(
                {
                    "name": file,
                    "size": size_str,
                    "modified": mod_time,
                    "path": full_path,
                }
            )
        # Ordenar y limitar a 20 más recientes
        backup_files.sort(key=lambda x: x["modified"], reverse=True)
        return backup_files[:20]
    except (OSError, PermissionError) as e:
        logger.error(f"Error al obtener archivos de backup: {str(e)}", exc_info=True)
        return []


@admin_bp.route("/usuarios")
@admin_required
def lista_usuarios():
    try:
        # Obtener el término de búsqueda
        q = request.args.get("q", "").strip()
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.dashboard_admin"))
        if q:
            # Búsqueda insensible a mayúsculas/minúsculas en email o nombre de usuario
            usuarios = list(
                users_col.find(
                    {
                        "$or": [
                            {"email": {"$regex": q, "$options": "i"}},
                            {"username": {"$regex": q, "$options": "i"}},
                            {"nombre": {"$regex": q, "$options": "i"}},
                        ]
                    }
                )
            )
        else:
            usuarios = list(users_col.find())
        # Ordenar usuarios por nombre alfabéticamente
        usuarios.sort(key=lambda u: u.get("nombre", "").lower())
        # Obtener catálogos para calcular cuántos tiene cada usuario
        from app.extensions import mongo

        collections_to_check = ["catalogs", "spreadsheets"]
        for user in usuarios:
            posibles = {
                user.get("email"),
                user.get("username"),
                user.get("name"),
                user.get("nombre"),
            }
            posibles = {v for v in posibles if v}
            total_count = 0
            for collection_name in collections_to_check:
                try:
                    if mongo and mongo.db is not None:
                        collection = mongo.db[collection_name]
                    else:
                        continue
                    query = {"$or": []}
                    for val in posibles:
                        query["$or"].extend(
                            [
                                {"created_by": val},
                                {"owner": val},
                                {"owner_name": val},
                                {"email": val},
                                {"username": val},
                                {"name": val},
                            ]
                        )
                    count = collection.count_documents(query)
                    total_count += count
                    logger.info(
                        f"[ADMIN] Usuario {user.get('email')} tiene {count} catálogos en {collection_name}"
                    )
                except (AttributeError, KeyError, TypeError) as e:
                    logger.error(
                        f"Error al contar catálogos en {collection_name}: {str(e)}"
                    )
            user["num_catalogs"] = total_count
            logger.info(
                f"[ADMIN] Usuario {user.get('email')} tiene un total de {total_count} catálogos"
            )
        # Calcular estadísticas
        stats = {
            "total": len(usuarios),
            "roles": {
                "admin": sum(1 for u in usuarios if u.get("role") == "admin"),
                "normal": sum(1 for u in usuarios if u.get("role") == "user"),
                "no_role": sum(1 for u in usuarios if not u.get("role")),
            },
        }
        return render_template("admin/users.html", usuarios=usuarios, stats=stats)
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"Error en lista_usuarios: {str(e)}", exc_info=True)
        flash(f"Error al cargar la lista de usuarios: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route("/usuarios/<user_email>/catalogos")
@admin_required
def ver_catalogos_usuario(user_email: str):
    try:
        # Verificar que el usuario existe
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.lista_usuarios"))
        user = users_col.find_one({"email": user_email})
        if not user:
            flash(f"Usuario con email {user_email} no encontrado", "error")
            return redirect(url_for("admin.lista_usuarios"))
        # Unificar criterio: buscar por todos los posibles identificadores
        posibles = {
            user.get("email"),
            user.get("username"),
            user.get("name"),
            user.get("nombre"),
        }
        posibles = {v for v in posibles if v}
        from app.extensions import mongo

        collections_to_check = ["catalogs", "spreadsheets"]
        all_catalogs = []
        for collection_name in collections_to_check:
            try:
                if mongo and mongo.db is not None:
                    collection = mongo.db[collection_name]
                else:
                    continue
                query: Dict[str, Any] = {"$or": []}
                for val in posibles:
                    query["$or"].extend(
                        [
                            {"created_by": val},
                            {"owner": val},
                            {"owner_name": val},
                            {"email": val},
                            {"username": val},
                            {"name": val},
                        ]
                    )
                catalogs_cursor = collection.find(query)
                for catalog in catalogs_cursor:
                    catalog["collection_source"] = collection_name
                    all_catalogs.append(catalog)
                logger.info(
                    f"[ADMIN] Encontrados {collection.count_documents(query)} catálogos en {collection_name} para {posibles}"
                )
            except (AttributeError, KeyError, TypeError) as e:
                logger.error(
                    f"Error al buscar catálogos en {collection_name}: {str(e)}"
                )
        catalogs = all_catalogs
        logger.info(
            f"[ADMIN] Total de catálogos encontrados para {posibles}: {len(catalogs)}"
        )
        # Añadir _id_str a cada catálogo para facilitar su uso en las plantillas
        for catalog in catalogs:
            catalog["_id_str"] = str(catalog["_id"])
            # Calcular el número de filas del catálogo
            if "rows" in catalog:
                catalog["row_count"] = len(catalog["rows"])
            elif "data" in catalog:
                catalog["row_count"] = len(catalog["data"])
            else:
                catalog["row_count"] = 0
            # Formatear la fecha de creación
            if "created_at" in catalog and catalog["created_at"]:
                if isinstance(catalog["created_at"], str):
                    catalog["created_at_formatted"] = catalog["created_at"]
                else:
                    catalog["created_at_formatted"] = catalog["created_at"].strftime(
                        "%d/%m/%Y %H:%M"
                    )
            else:
                catalog["created_at_formatted"] = "N/A"
        return render_template(
            "admin/catalogos_usuario.html", user=user, catalogs=catalogs
        )
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"Error en ver_catalogos_usuario: {str(e)}", exc_info=True)
        flash(f"Error al cargar los catálogos del usuario: {str(e)}", "error")
        # Intentar recuperar el usuario incluso en caso de error
        try:
            users_col = get_users_collection()
            if users_col is not None:
                user = users_col.find_one({"email": user_email})
                if user:
                    return render_template(
                        "admin/catalogos_usuario.html", user=user, catalogs=[]
                    )
        except (AttributeError, KeyError, TypeError) as inner_e:
            logger.error(f"Error secundario al recuperar usuario: {str(inner_e)}")
        return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/usuarios/catalogo/<catalog_id>")
@admin_required
def ver_catalogo_admin(catalog_id: str):
    try:
        # Obtener el catálogo
        from bson.objectid import ObjectId

        from app.extensions import mongo

        if mongo and mongo.db is not None:
            catalog = mongo.db.catalogs.find_one({"_id": ObjectId(catalog_id)})
        else:
            catalog = None
        if not catalog:
            flash(f"Catálogo con ID {catalog_id} no encontrado", "error")
            return redirect(url_for("admin.lista_usuarios"))

        # Añadir _id_str al catálogo
        catalog["_id_str"] = str(catalog["_id"])

        return render_template("admin/ver_catalogo.html", catalog=catalog)
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"Error en ver_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al cargar el catálogo: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/usuarios/delete/<user_id>", methods=["POST"])
@admin_required
def eliminar_usuario(user_id: str):
    users_col = get_users_collection()
    if users_col is not None:
        users_col.delete_one({"_id": ObjectId(user_id)})
        flash("Usuario eliminado", "success")
    else:
        flash("Error: No se pudo acceder a la colección de usuarios", "error")
    return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/usuarios/edit/<user_id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(user_id: str):
    try:
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.lista_usuarios"))
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("admin.lista_usuarios"))

        if request.method == "POST":
            # Verificar si es una solicitud de verificación desde la página verify_users
            verified = request.form.get("verified")
            if verified == "true":
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"verified": True, "updated_at": datetime.now()}},
                )
                flash(
                    f"Usuario {user.get('nombre', 'desconocido')} ha sido verificado",
                    "success",
                )
                # Registrar en el log de auditoría
                audit_log(
                    "user_verified",
                    user_id=session.get("user_id"),
                    details={
                        "verified_user_email": user.get("email"),
                        "verified_by": session.get("username"),
                        "verified_user_name": user.get("nombre", "desconocido"),
                    },
                )
                return redirect(url_for("admin.verify_users"))

            # Procesamiento normal de edición de usuario
            nombre = request.form.get("nombre")
            email = request.form.get("email")
            role = request.form.get("role", "user")
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            verified_status = request.form.get("verified_status") == "on"

            # Validar que el nombre y email no estén vacíos
            if not nombre or not email:
                flash("El nombre y el correo son requeridos", "error")
                return redirect(url_for("admin.editar_usuario", user_id=user_id))

            # Verificar si el email ya existe para otro usuario
            email_changed = email.lower() != user.get("email", "").lower()
            email_conflict = False

            if email_changed:
                # Buscar si el email ya existe para otro usuario
                existing_user = users_col.find_one(
                    {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}
                )

                if existing_user and str(existing_user.get("_id")) != user_id:
                    email_conflict = True
                    flash(
                        f"El correo electrónico {email} ya está en uso por otro usuario",
                        "error",
                    )
                    logger.warning(
                        f"Intento de actualizar usuario {user_id} con email duplicado: {email}"
                    )

            # Si se proporcionó una nueva contraseña
            if new_password:
                if new_password != confirm_password:
                    flash("Las contraseñas no coinciden", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Verificar que la contraseña cumpla con los requisitos
                if len(new_password) < 8:
                    flash("La contraseña debe tener al menos 8 caracteres", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Actualizar la contraseña
                password_hash = generate_password_hash(new_password)
                users_col.update_one(
                    {"_id": ObjectId(user_id)}, {"$set": {"password": password_hash}}
                )
                flash("Contraseña actualizada", "success")

            # Si hay conflicto de email, no actualizar nada más
            if email_conflict:
                return redirect(url_for("admin.editar_usuario", user_id=user_id))

            # Actualizar otros campos
            update_data = {
                "nombre": nombre,
                "role": role,
                "verified": verified_status,
                "updated_at": datetime.now(),
            }

            # Solo actualizar el email si ha cambiado
            if email_changed:
                update_data["email"] = email

            # Realizar la actualización
            _ = users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for("admin.lista_usuarios"))

        return render_template("admin/editar_usuario.html", usuario=user)
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error al editar usuario {user_id}: {str(e)}", exc_info=True)
        flash(f"Error al editar usuario: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/usuarios/create", methods=["GET", "POST"])
@admin_required
def crear_usuario():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "user")

        if not all([nombre, email, password]):
            flash("Todos los campos son requeridos", "error")
            return render_template("admin/crear_usuario.html")

        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return render_template("admin/crear_usuario.html")

        existing_user = users_col.find_one({"email": email})

        if existing_user:
            flash("Ya existe un usuario con este email", "error")
            return render_template("admin/crear_usuario.html")

        # Aquí deberías implementar la lógica para hashear la contraseña
        # Por ahora, usaremos el password directamente
        user_data = {
            "nombre": nombre,
            "email": email,
            "password": password,  # En producción, hashea esto
            "role": role,
            "num_tables": 0,
            "tables_updated_at": None,
            "last_ip": "",
            "last_login": None,
            "updated_at": None,
            "failed_attempts": 0,
            "locked_until": None,
        }

        _ = users_col.insert_one(user_data)
        flash("Usuario creado exitosamente", "success")
        return redirect(url_for("admin.lista_usuarios"))

    return render_template("admin/crear_usuario.html")


@admin_bp.route("/backup/json")
def backup_json():
    catalog = get_catalogs_collection()
    if catalog is None:
        flash("Error: No se pudo acceder a la colección de catálogos", "error")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    data = list(catalog.find())
    for d in data:
        d["_id"] = str(d["_id"])
    output = io.StringIO()
    json.dump(data, output, indent=4, default=str)
    output.seek(0)
    # Guardar el archivo en /backups/ con nombre único
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir, exist_ok=True)
    filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = os.path.join(backups_dir, filename)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    # Subir a Google Drive
    try:
        enlace_drive = upload_to_drive(backup_path)
        os.remove(backup_path)
        flash(
            f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>",
            "success",
        )
        audit_log(
            "backup_json_uploaded_to_drive",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "username": session.get("username", "desconocido"),
                "drive_url": enlace_drive,
            },
        )
    except (OSError, PermissionError, ValueError) as e:
        flash(
            f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.",
            "danger",
        )
        audit_log(
            "backup_json_upload_failed",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "username": session.get("username", "desconocido"),
                "error": str(e),
            },
            success=False,
        )
    # Permitir descarga directa como antes
    return send_file(
        io.BytesIO(output.read().encode()),
        download_name="backup_catalog.json",
        as_attachment=True,
    )


@admin_bp.route("/backup/csv")
def backup_csv():
    catalog = get_catalogs_collection()
    if catalog is None:
        flash("Error: No se pudo acceder a la colección de catálogos", "error")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    data = list(catalog.find())
    if not data:
        flash("No hay datos para exportar", "warning")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    # Unificar todos los campos presentes en los documentos
    all_fields = set()
    for row in data:
        all_fields.update(row.keys())
    headers = list(all_fields)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in data:
        row["_id"] = str(row["_id"])
        row_filled = {k: row.get(k, "") for k in headers}
        writer.writerow(row_filled)
    output.seek(0)
    # Guardar el archivo en /backups/ con nombre único
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir, exist_ok=True)
    filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    backup_path = os.path.join(backups_dir, filename)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    # Subir a Google Drive
    try:
        enlace_drive = upload_to_drive(backup_path)
        os.remove(backup_path)
        flash(
            f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>",
            "success",
        )
        audit_log(
            "backup_csv_uploaded_to_drive",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "username": session.get("username", "desconocido"),
                "drive_url": enlace_drive,
            },
        )
    except (OSError, PermissionError, ValueError) as e:
        flash(
            f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.",
            "danger",
        )
        audit_log(
            "backup_csv_upload_failed",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "username": session.get("username", "desconocido"),
                "error": str(e),
            },
            success=False,
        )
    # Permitir descarga directa como antes
    return send_file(
        io.BytesIO(output.read().encode()),
        download_name="backup_catalog.csv",
        as_attachment=True,
    )


@admin_bp.route("/backups/cleanup", methods=["POST"])
@admin_required
def cleanup_old_backups():
    """Elimina backups antiguos según la fecha o cantidad máxima permitida."""
    days = int(request.form.get("days", 30))
    max_files = int(request.form.get("max_files", 20))
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        flash("No hay backups para limpiar", "info")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    files = [
        os.path.join(backups_dir, f)
        for f in os.listdir(backups_dir)
        if os.path.isfile(os.path.join(backups_dir, f))
    ]
    # Ordenar por fecha de modificación descendente
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    now = datetime.now()
    removed = 0
    # Eliminar archivos más antiguos que X días
    for f in files:
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        if (now - mtime) > timedelta(days=days):
            try:
                os.remove(f)
                removed += 1
                logger.info(f"Backup eliminado por antigüedad: {f}")
            except (OSError, PermissionError) as e:
                logger.error(f"Error al eliminar backup {f}: {e}")
    # Si hay más de max_files, eliminar los más antiguos
    files = [
        os.path.join(backups_dir, f)
        for f in os.listdir(backups_dir)
        if os.path.isfile(os.path.join(backups_dir, f))
    ]
    if len(files) > max_files:
        for f in files[max_files:]:
            try:
                os.remove(f)
                removed += 1
                logger.info(f"Backup eliminado por exceso de cantidad: {f}")
            except (OSError, PermissionError) as e:
                logger.error(f"Error al eliminar backup {f}: {e}")
    flash(f"Backups antiguos eliminados: {removed}", "info")
    audit_log(
        "backup_cleanup",
        user_id=session.get("user_id"),
        details={
            "username": session.get("username", "desconocido"),
            "days": days,
            "max_files": max_files,
            "removed_count": removed,
        },
    )
    return redirect(url_for("maintenance.maintenance_dashboard"))


@admin_bp.route("/cleanup_resets")
@admin_required
def cleanup_resets():
    reset_tokens_col = get_reset_tokens_collection()
    if reset_tokens_col is None:
        flash("Error: No se pudo acceder a la colección de tokens", "error")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    result = reset_tokens_col.delete_many({"used": True})
    flash(f"Tokens eliminados: {result.deleted_count}", "info")

    # Registrar la limpieza en las métricas
    if "cleanup_history" not in monitoring._app_metrics:
        monitoring._app_metrics["cleanup_history"] = []

    monitoring._app_metrics["cleanup_history"].append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "tokens_reset",
            "count": result.deleted_count,
        }
    )
    monitoring.save_metrics()

    return redirect(url_for("maintenance.maintenance_dashboard"))


# API para limpieza de archivos temporales antiguos
@admin_bp.route("/delete-temp-files", methods=["POST"])
@admin_required
def delete_temp_files_route():
    selected = request.form.getlist("temp_files")
    if not selected:
        flash("No se seleccionaron archivos para borrar", "warning")
        return redirect(url_for("admin.system_status"))
    removed = delete_temp_files(selected)
    flash(f"Archivos temporales eliminados: {removed}", "success")
    return redirect(url_for("admin.system_status"))


@admin_bp.route("/api/cleanup-temp", methods=["POST"])
@admin_required
def api_cleanup_temp():
    days = request.form.get("days", 7, type=int)
    result = monitoring.cleanup_old_temp_files(days)

    # Registrar la limpieza en las métricas
    if "cleanup_history" not in monitoring._app_metrics:
        monitoring._app_metrics["cleanup_history"] = []

    monitoring._app_metrics["cleanup_history"].append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "temp_files",
            "days": days,
            "files_removed": result.get("files_removed", 0),
            "bytes_removed": result.get("bytes_removed", 0),
        }
    )
    monitoring.save_metrics()

    return jsonify(
        {
            "success": True,
            "message": f"Se eliminaron {result.get('files_removed', 0)} archivos temporales",
            "details": result,
        }
    )


# API para obtener el estado del sistema (moved to end of file)


# API para truncar archivos de log
@admin_bp.route("/api/truncate-logs", methods=["POST"])
@admin_required
def api_truncate_logs():
    try:
        # Obtener datos de la solicitud
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No se proporcionaron datos"})

        log_files = data.get("logFiles", []) if isinstance(data, dict) else []
        method = (
            data.get("method", "complete") if isinstance(data, dict) else "complete"
        )

        if not log_files:
            return jsonify(
                {"status": "error", "message": "No se especificaron archivos de log"}
            )

        # Verificar que los archivos existen y son válidos
        logs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../logs")
        )
        processed_files = []
        error_files = []

        for log_file in log_files:
            # Validar el nombre del archivo para evitar ataques de traversal de directorio
            if ".." in log_file or "/" in log_file or "\\" in log_file:
                error_files.append(f"{log_file} (nombre de archivo no válido)")
                continue

            log_path = os.path.join(logs_dir, log_file)
            if not os.path.exists(log_path):
                error_files.append(f"{log_file} (no existe)")
                continue

            try:
                if method == "complete":
                    # Truncado completo
                    with open(log_path, "w") as f:
                        f.truncate(0)
                    processed_files.append(log_file)
                    logger.info(f"Archivo de log {log_file} truncado completamente")

                elif method == "lines":
                    # Mantener últimas N líneas
                    try:
                        line_count = int(
                            data.get("lineCount", 100)
                            if isinstance(data, dict)
                            else 100
                        )
                        if line_count < 10:
                            line_count = 10  # Mínimo 10 líneas
                    except (ValueError, TypeError):
                        line_count = 100  # Valor predeterminado si hay un error

                    try:
                        with open(log_path, encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()

                        # Mantener solo las últimas N líneas
                        if len(lines) > line_count:
                            with open(log_path, "w", encoding="utf-8") as f:
                                f.writelines(lines[-line_count:])
                            logger.info(
                                f"Archivo de log {log_file} truncado a las últimas {line_count} líneas"
                            )
                        else:
                            logger.info(
                                f"El archivo {log_file} tiene menos de {line_count} líneas, no se truncó"
                            )

                        processed_files.append(log_file)
                    except UnicodeDecodeError:
                        # Si hay problemas con la codificación, usar un enfoque binario
                        with open(log_path, "rb") as f:
                            f.seek(0, os.SEEK_END)
                            size = f.tell()

                            # Estimar el tamaño promedio de línea (100 bytes)
                            avg_line_size = 100
                            estimated_size = line_count * avg_line_size

                            # Si el archivo es más grande que el tamaño estimado, truncarlo
                            if size > estimated_size:
                                # Retroceder aproximadamente el número de líneas deseado
                                f.seek(-min(size, estimated_size * 2), os.SEEK_END)
                                # Leer el resto del archivo
                                data = f.read()

                                # Contar nuevas líneas y ajustar si es necesario
                                newlines = data.count(b"\n")
                                if newlines > line_count:
                                    # Encontrar la posición de la línea de inicio
                                    pos = 0
                                    for _i in range(newlines - line_count):
                                        next_pos = data.find(b"\n", pos) + 1
                                        if next_pos == 0:  # No se encontró
                                            break
                                        pos = next_pos

                                    # Escribir solo las últimas líneas
                                    with open(log_path, "wb") as f:
                                        f.write(data[pos:])

                                    logger.info(
                                        f"Archivo de log {log_file} truncado a aproximadamente las últimas {line_count} líneas (modo binario)"
                                    )
                                    processed_files.append(log_file)
                                else:
                                    logger.info(
                                        f"El archivo {log_file} tiene menos de {line_count} líneas, no se truncó"
                                    )
                                    processed_files.append(log_file)

                elif method == "date":
                    # Eliminar entradas anteriores a una fecha
                    cutoff_date = (
                        data.get("cutoffDate") if isinstance(data, dict) else None
                    )
                    if not cutoff_date:
                        error_files.append(
                            f"{log_file} (no se especificó fecha de corte)"
                        )
                        continue

                    # Convertir la fecha a un objeto datetime
                    try:
                        cutoff_date = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
                    except ValueError:
                        error_files.append(
                            f"{log_file} (formato de fecha inválido, use YYYY-MM-DD)"
                        )
                        continue

                    try:
                        with open(log_path, encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()

                        # Filtrar líneas por fecha
                        kept_lines = []
                        for line in lines:
                            # Intentar extraer la fecha de la línea de log (formato típico: [YYYY-MM-DD HH:MM:SS,mmm])
                            date_match = re.search(r"\[(\d{4}-\d{2}-\d{2})", line)
                            if date_match:
                                try:
                                    line_date_str = date_match.group(1)
                                    line_date = datetime.strptime(
                                        line_date_str, "%Y-%m-%d"
                                    ).date()
                                    if line_date >= cutoff_date:
                                        kept_lines.append(line)
                                except ValueError:
                                    # Si hay un error al parsear la fecha, mantener la línea
                                    kept_lines.append(line)
                            else:
                                # Si no se puede extraer la fecha, mantener la línea
                                kept_lines.append(line)

                        # Escribir las líneas filtradas de vuelta al archivo
                        with open(log_path, "w", encoding="utf-8") as f:
                            f.writelines(kept_lines)

                        logger.info(
                            f"Archivo de log {log_file} truncado a entradas posteriores a {cutoff_date}"
                        )
                        processed_files.append(log_file)
                    except UnicodeDecodeError:
                        error_files.append(
                            f"{log_file} (error de codificación, no se puede procesar por fecha)"
                        )
                        continue

                else:
                    error_files.append(f"{log_file} (método de truncado no válido)")
                    continue

            except (OSError, PermissionError, UnicodeError) as e:
                logger.error(
                    f"Error al truncar el archivo {log_file}: {str(e)}", exc_info=True
                )
                error_files.append(f"{log_file} (error: {str(e)})")

        # Registrar en el log de auditoría
        audit_log(
            f"Truncado de logs: {', '.join(processed_files)} usando método {method}"
        )

        # Preparar respuesta
        if error_files:
            return jsonify(
                {
                    "status": "partial",
                    "message": f"Se procesaron {len(processed_files)} archivos con éxito. Errores en {len(error_files)} archivos.",
                    "processed": processed_files,
                    "error_files": error_files,
                }
            )
        else:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Se truncaron {len(processed_files)} archivos de log correctamente.",
                    "processed": processed_files,
                    "error_files": [],
                }
            )

    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en api_truncate_logs: {str(e)}", exc_info=True)
        return jsonify(
            {
                "status": "error",
                "message": f"Error al truncar logs: {str(e)}",
                "error_files": [],
            }
        )


# API para eliminar archivos de backup
@admin_bp.route("/api/delete-backups", methods=["POST"])
@admin_required
def api_delete_backups():
    try:
        # Obtener datos de la solicitud
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No se proporcionaron datos"})

        backup_files = data.get("backupFiles", [])
        delete_criteria = data.get("deleteCriteria", "selected")

        if delete_criteria == "selected" and not backup_files:
            from flask import abort

            abort(
                400, description="No se especificaron archivos de backup para eliminar"
            )

        # Verificar que los archivos existen y son válidos
        backup_dir = os.path.abspath(os.path.join(os.getcwd(), "backups"))
        logger.info(f"API Delete - Directorio de backups: {backup_dir}")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)

        processed_files = []
        error_files = []

        # Obtener todos los archivos de backup si el criterio es por fecha o todos
        all_backup_files = []
        if delete_criteria in ["date", "all"]:
            all_backup_files = get_backup_files(backup_dir)

        if delete_criteria == "selected":
            # Eliminar archivos seleccionados
            for backup_file in backup_files:
                # Validar el nombre del archivo para evitar ataques de traversal de directorio
                if ".." in backup_file:
                    error_files.append(f"{backup_file} (nombre de archivo no válido)")
                    continue

                # Manejar archivos en subdirectorios
                backup_path = os.path.join(backup_dir, backup_file)
                if not os.path.exists(backup_path):
                    error_files.append(f"{backup_file} (no existe)")
                    continue

                try:
                    os.remove(backup_path)
                    processed_files.append(backup_file)
                    logger.info(
                        f"Archivo de backup {backup_file} eliminado correctamente"
                    )
                except (OSError, PermissionError) as e:
                    logger.error(
                        f"Error al eliminar el archivo {backup_file}: {str(e)}",
                        exc_info=True,
                    )
                    error_files.append(f"{backup_file} (error: {str(e)})")

        elif delete_criteria == "date":
            # Eliminar archivos anteriores a una fecha
            cutoff_date = data.get("cutoffDate")
            if not cutoff_date:
                return jsonify(
                    {"status": "error", "message": "No se especificó fecha de corte"}
                )

            try:
                cutoff_date = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify(
                    {
                        "status": "error",
                        "message": "Formato de fecha inválido, use YYYY-MM-DD",
                    }
                )

            for backup_file in all_backup_files:
                try:
                    file_date = datetime.strptime(
                        backup_file["modified"], "%Y-%m-%d %H:%M:%S"
                    ).date()
                    if file_date < cutoff_date:
                        os.remove(backup_file["path"])
                        processed_files.append(backup_file["name"])
                        logger.info(
                            f"Archivo de backup {backup_file['name']} eliminado (anterior a {cutoff_date})"
                        )
                except (OSError, PermissionError, ValueError) as e:
                    logger.error(
                        f"Error al procesar el archivo {backup_file['name']}: {str(e)}",
                        exc_info=True,
                    )
                    error_files.append(f"{backup_file['name']} (error: {str(e)})")

        elif delete_criteria == "all":
            # Eliminar todos los archivos de backup
            for backup_file in all_backup_files:
                try:
                    os.remove(backup_file["path"])
                    processed_files.append(backup_file["name"])
                    logger.info(
                        f"Archivo de backup {backup_file['name']} eliminado (eliminación total)"
                    )
                except (OSError, PermissionError) as e:
                    logger.error(
                        f"Error al eliminar el archivo {backup_file['name']}: {str(e)}",
                        exc_info=True,
                    )
                    error_files.append(f"{backup_file['name']} (error: {str(e)})")

        else:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Criterio de eliminación no válido: {delete_criteria}",
                }
            )

        # Registrar en el log de auditoría
        audit_log(
            f"Eliminación de backups: {', '.join(processed_files)} usando criterio {delete_criteria}"
        )

        # Preparar respuesta
        if error_files:
            return jsonify(
                {
                    "status": "partial",
                    "message": f"Se eliminaron {len(processed_files)} archivos, pero hubo errores con {len(error_files)} archivos",
                    "processed": processed_files,
                    "error_files": error_files,
                }
            )
        else:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Se eliminaron {len(processed_files)} archivos correctamente",
                    "processed": processed_files,
                    "error_files": [],
                }
            )

    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en api_delete_backups: {str(e)}", exc_info=True)
        return jsonify(
            {"status": "error", "message": f"Error al procesar la solicitud: {str(e)}"}
        )


# Ruta para descargar un archivo de log específico
@admin_bp.route("/logs/download/<filename>")
@admin_required
def download_log(filename: str):
    try:
        # Validar el nombre del archivo
        if ".." in filename or "/" in filename or "\\" in filename:
            flash("Nombre de archivo no válido", "danger")
            return redirect(url_for("admin.system_status"))

        logs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../logs")
        )
        log_path = os.path.join(logs_dir, filename)

        if not os.path.exists(log_path):
            flash(f"El archivo {filename} no existe", "danger")
            return redirect(url_for("admin.system_status"))

        # Registrar en el log de auditoría
        audit_log("log_file_download", details={"filename": filename})

        return send_file(log_path, as_attachment=True, download_name=filename)
    except (OSError, PermissionError) as e:
        logger.error(f"Error al descargar log {filename}: {str(e)}", exc_info=True)
        flash(f"Error al descargar el archivo: {str(e)}", "danger")
        return redirect(url_for("admin.system_status"))


# Ruta para descargar múltiples archivos de log en un ZIP
@admin_bp.route("/logs/download-multiple")
@admin_required
def download_multiple_logs():
    try:
        files_param = request.args.get("files", "")
        if not files_param:
            flash("No se especificaron archivos para descargar", "danger")
            return redirect(url_for("admin.system_status"))

        files = files_param.split(",")
        logs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../logs")
        )

        # Crear un archivo ZIP temporal
        import tempfile
        import zipfile

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_file.close()

        with zipfile.ZipFile(temp_file.name, "w") as zipf:
            for filename in files:
                # Validar el nombre del archivo
                if ".." in filename or "/" in filename or "\\" in filename:
                    continue

                log_path = os.path.join(logs_dir, filename)
                if os.path.exists(log_path):
                    zipf.write(log_path, arcname=filename)

        # Registrar en el log de auditoría
        audit_log("multiple_log_files_download", details={"files": files})

        return send_file(temp_file.name, as_attachment=True, download_name="logs.zip")
    except (OSError, PermissionError) as e:
        logger.error(f"Error al descargar múltiples logs: {str(e)}", exc_info=True)
        flash(f"Error al descargar los archivos: {str(e)}", "danger")
        return redirect(url_for("admin.system_status"))


@admin_bp.route("/notification-settings", methods=["GET", "POST"])
@admin_required
def notification_settings():
    """Página de configuración de notificaciones"""
    if request.method == "POST":
        # Validar campos obligatorios y tipos
        required_fields = [
            "smtp_server",
            "smtp_port",
            "smtp_username",
            "threshold_cpu",
            "threshold_memory",
            "threshold_disk",
            "threshold_error_rate",
            "cooldown",
        ]
        missing_fields = [f for f in required_fields if not request.form.get(f)]
        int_fields = [
            "smtp_port",
            "threshold_cpu",
            "threshold_memory",
            "threshold_disk",
            "threshold_error_rate",
            "cooldown",
        ]
        invalid_ints = []
        for f in int_fields:
            val = request.form.get(f)
            if val is not None and val != "":
                try:
                    int(val)
                except (ValueError, TypeError):
                    invalid_ints.append(f)
            else:
                invalid_ints.append(f)
        if missing_fields or invalid_ints:
            flash(
                f"Error: Faltan campos obligatorios o valores inválidos: {', '.join(set(missing_fields + invalid_ints))}",
                "danger",
            )
            return redirect(url_for("admin.notification_settings"))

        enabled = request.form.get("enable_notifications") == "on"
        use_api = request.form.get("use_api") == "on"

        # Configuración SMTP
        smtp_settings = {
            "server": request.form.get("smtp_server"),
            "port": int(request.form.get("smtp_port") or "587"),
            "username": request.form.get("smtp_username"),
            "use_tls": request.form.get("smtp_tls") == "on",
        }
        password = request.form.get("smtp_password")
        if password:
            smtp_settings["password"] = password

        # Configuración API de Brevo
        brevo_api_settings = {
            "api_key": request.form.get("brevo_api_key"),
            "sender_name": request.form.get("sender_name"),
            "sender_email": request.form.get("sender_email"),
        }

        recipients = [r for r in request.form.getlist("recipients") if r.strip()]
        thresholds = {
            "cpu": int(request.form.get("threshold_cpu") or "80"),
            "memory": int(request.form.get("threshold_memory") or "80"),
            "disk": int(request.form.get("threshold_disk") or "80"),
            "error_rate": int(request.form.get("threshold_error_rate") or "10"),
        }
        cooldown = int(request.form.get("cooldown") or "300")

        if notifications.update_settings(
            enabled=enabled,
            use_api=use_api,
            smtp_settings=smtp_settings,
            brevo_api_settings=brevo_api_settings,
            recipients=recipients,
            thresholds=thresholds,
            cooldown=cooldown,
        ):
            flash(
                "Configuración de notificaciones actualizada correctamente", "success"
            )
            audit_log(
                "notification_settings_updated",
                details={
                    "enabled": enabled,
                    "smtp_server": smtp_settings["server"],
                    "recipients_count": len(recipients),
                },
            )
        else:
            flash("Error al guardar la configuración de notificaciones", "danger")
        return redirect(url_for("admin.notification_settings"))
    config = notifications.get_settings()
    return render_template("admin/notification_settings.html", config=config)


@admin_bp.route("/api/test-email", methods=["POST"])
@admin_required
def test_email():
    """Enviar correo de prueba usando las credenciales del archivo .env"""
    email = request.form.get("email")
    if not email:
        return jsonify(
            {"success": False, "error": "No se proporcionó dirección de correo"}
        )

    try:
        # Registrar información sobre el intento de envío
        logger.info(f"[ADMIN] Intentando enviar correo de prueba a {email}")

        # Mostrar las variables de entorno relacionadas con el correo (sin la contraseña)
        mail_server = os.environ.get("MAIL_SERVER")
        mail_port = os.environ.get("MAIL_PORT")
        mail_username = os.environ.get("MAIL_USERNAME")
        mail_use_tls = os.environ.get("MAIL_USE_TLS")
        mail_default_sender = os.environ.get("MAIL_DEFAULT_SENDER")
        mail_default_sender_name = os.environ.get("MAIL_DEFAULT_SENDER_NAME")
        mail_default_sender_email = os.environ.get("MAIL_DEFAULT_SENDER_EMAIL")

        logger.info(
            f"[ADMIN] Configuración de correo: Servidor={mail_server}, Puerto={mail_port}, "
            f"Usuario={mail_username}, TLS={mail_use_tls}"
        )
        logger.info(
            f"[ADMIN] Remitentes configurados: DEFAULT_SENDER={mail_default_sender}, "
            f"SENDER_NAME={mail_default_sender_name}, SENDER_EMAIL={mail_default_sender_email}"
        )

        # Crear un correo de prueba extremadamente simple para diagnosticar el problema
        import smtplib
        from email.mime.text import MIMEText

        try:
            # Crear un mensaje simple de texto plano
            logger.info("[ADMIN] Creando mensaje de prueba simple...")
            msg = MIMEText("Este es un mensaje de prueba.")
            msg["Subject"] = "Prueba de correo desde edefrutos2025"
            msg["From"] = mail_username or "noreply@example.com"
            msg["To"] = email

            # Intentar enviar directamente
            logger.info(f"[ADMIN] Conectando a {mail_server}:{mail_port}...")
            server = smtplib.SMTP(mail_server or "localhost", int(mail_port or "587"))

            if mail_use_tls and mail_use_tls.lower() in ("true", "1", "t"):
                logger.info("[ADMIN] Iniciando TLS...")
                server.starttls()

            logger.info(f"[ADMIN] Iniciando sesión con {mail_username}...")
            server.login(mail_username or "", os.environ.get("MAIL_PASSWORD") or "")

            logger.info("[ADMIN] Enviando mensaje...")
            server.send_message(msg)

            logger.info("[ADMIN] Cerrando conexión...")
            server.quit()

            logger.info(
                f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método directo"
            )
            audit_log(
                "test_email_sent", details={"recipient": email, "method": "direct"}
            )
            return jsonify({"success": True})
        except (ConnectionError, TimeoutError, OSError, ValueError) as direct_err:
            logger.error(
                f"[ADMIN] Error en método directo: {str(direct_err)}", exc_info=True
            )

            # Si el método directo falla, intentar con el método normal
            logger.info("[ADMIN] Intentando con el método normal...")
            result = notifications.send_test_email(email)

            if result:
                logger.info(
                    f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método normal"
                )
                audit_log(
                    "test_email_sent", details={"recipient": email, "method": "normal"}
                )
                return jsonify({"success": True})
            else:
                logger.error(
                    f"[ADMIN] Error al enviar correo de prueba a {email}. Ambos métodos fallaron."
                )
                return jsonify(
                    {
                        "success": False,
                        "error": f"Error directo: {str(direct_err)}. Error en método normal: Resultado falso sin excepción. Revisa los logs para más detalles.",
                    }
                )
    except (ConnectionError, TimeoutError, OSError, ValueError, AttributeError) as e:
        logger.error(
            f"[ADMIN] Excepción al enviar correo de prueba a {email}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"success": False, "error": f"Error: {str(e)}"})


@admin_bp.route("/verify-users")
@admin_required
def verify_users():
    try:
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("maintenance.maintenance_dashboard"))
        usuarios = list(users_col.find())
        # Contar usuarios verificados y no verificados
        verified_count = sum(1 for user in usuarios if user.get("verified", False))
        unverified_count = len(usuarios) - verified_count
        # Estadísticas de usuarios
        stats = {
            "total": len(usuarios),
            "verified": verified_count,
            "unverified": unverified_count,
        }
        # Obtener usuarios no verificados para mostrarlos en la interfaz
        unverified_users = [
            user for user in usuarios if not user.get("verified", False)
        ]
        return render_template(
            "admin/verify_users.html", stats=stats, unverified_users=unverified_users
        )
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en verify_users: {str(e)}", exc_info=True)
        flash(f"Error al verificar usuarios: {str(e)}", "error")
        return redirect(url_for("maintenance.maintenance_dashboard"))


@admin_bp.route("/bulk_user_action", methods=["POST"])
@admin_required
def bulk_user_action():
    try:
        user_ids = request.form.getlist("user_ids")
        action = request.form.get("action")
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.verify_users"))
        if not user_ids or not action:
            flash("Debes seleccionar usuarios y una acción.", "warning")
            return redirect(url_for("admin.verify_users"))
        from bson import ObjectId

        object_ids = [ObjectId(uid) for uid in user_ids if uid]
        if action == "verify":
            result = users_col.update_many(
                {"_id": {"$in": object_ids}}, {"$set": {"verified": True}}
            )
            flash(f"{result.modified_count} usuarios verificados.", "success")
        elif action == "delete":
            result = users_col.delete_many({"_id": {"$in": object_ids}})
            flash(f"{result.deleted_count} usuarios eliminados.", "success")
        else:
            flash("Acción no reconocida.", "danger")
        return redirect(url_for("admin.verify_users"))
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en bulk_user_action: {str(e)}", exc_info=True)
        flash(f"Error al procesar la acción masiva: {str(e)}", "danger")
        return redirect(url_for("admin.verify_users"))


@admin_bp.route("/catalogos-usuario/<user_id>")
@admin_required
def ver_catalogos_usuario_por_id(user_id: str):
    try:
        # Verificar que el usuario existe
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.lista_usuarios"))
        usuario = users_col.find_one({"_id": ObjectId(user_id)})
        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for("admin.lista_usuarios"))

        # Obtener todos los posibles identificadores del usuario
        user_email = usuario.get("email", "")
        username = usuario.get("username", "")
        nombre = usuario.get("name", "")
        posibles = {user_email, username, nombre}
        posibles = {v for v in posibles if v}
        logger.info(
            f"[ADMIN] Buscando catálogos para el usuario con ID: {user_id}, posibles: {posibles}"
        )

        # Obtener los catálogos del usuario de ambas colecciones
        collections_to_check = ["catalogs", "spreadsheets"]
        all_catalogs = []

        for collection_name in collections_to_check:
            try:
                db = get_mongo_db()
                if db is None:
                    continue
                collection = db[collection_name]
                # Buscar por todos los campos posibles
                query: Dict[str, Any] = {"$or": []}
                for val in posibles:
                    query["$or"].extend(
                        [
                            {"created_by": val},
                            {"owner": val},
                            {"owner_name": val},
                            {"email": val},
                            {"username": val},
                            {"name": val},
                        ]
                    )
                catalogs_cursor = collection.find(query)
                for catalog in catalogs_cursor:
                    catalog["collection_source"] = collection_name
                    catalog["_id_str"] = str(catalog["_id"])
                    all_catalogs.append(catalog)
                logger.info(
                    f"[ADMIN] Encontrados {collection.count_documents(query)} catálogos en {collection_name} para {posibles}"
                )
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                logger.error(
                    f"Error al buscar catálogos en {collection_name}: {str(e)}"
                )

        catalogs = all_catalogs
        logger.info(
            f"[ADMIN] Total de catálogos encontrados para {posibles}: {len(catalogs)}"
        )

        # Añadir información adicional a cada catálogo
        for catalog in catalogs:
            if "rows" in catalog and catalog["rows"] is not None:
                catalog["row_count"] = len(catalog["rows"])
            elif "data" in catalog and catalog["data"] is not None:
                catalog["row_count"] = len(catalog["data"])
            else:
                catalog["row_count"] = 0
            if "created_at" in catalog and catalog["created_at"]:
                try:
                    if hasattr(catalog["created_at"], "strftime"):
                        catalog["created_at_formatted"] = catalog[
                            "created_at"
                        ].strftime("%d/%m/%Y %H:%M")
                    else:
                        catalog["created_at_formatted"] = str(catalog["created_at"])
                except (AttributeError, ValueError, TypeError) as e:
                    logger.error(f"Error al formatear fecha: {str(e)}")
                    catalog["created_at_formatted"] = str(catalog["created_at"])
            else:
                catalog["created_at_formatted"] = "Fecha desconocida"

        return render_template(
            "admin/catalogos_usuario.html", catalogs=catalogs, user=usuario
        )
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en ver_catalogos_usuario: {str(e)}", exc_info=True)
        flash(f"Error al cargar los catálogos del usuario: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/catalogo/<collection_source>/<catalog_id>")
@admin_required
def ver_catalogo_unificado(collection_source: str, catalog_id: str):
    logger.info(
        f"[ADMIN] Entrando en ver_catalogo_unificado con collection_source={collection_source}, catalog_id={catalog_id}"
    )
    try:
        db = get_mongo_db()
        if db is None:
            flash("Error: No se pudo acceder a la base de datos", "error")
            return redirect(url_for("admin.dashboard_admin"))
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            logger.warning(
                f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
            )
            flash("Catálogo no encontrado", "warning")
            return render_template(
                "admin/ver_catalogo.html", catalog=None, error="Catálogo no encontrado"
            )
        # Refuerzo: asegurar que headers siempre exista y sea lista
        if "headers" not in catalog or not isinstance(catalog["headers"], list):
            catalog["headers"] = []
        # Refuerzo: asegurar que rows siempre exista y sea lista
        if ("rows" not in catalog or catalog["rows"] is None) and (
            "data" in catalog and isinstance(catalog["data"], list)
        ):
            catalog["rows"] = catalog["data"]
        elif "rows" not in catalog or catalog["rows"] is None:
            catalog["rows"] = []
        # Añadir información sobre la colección de origen
        catalog["collection_source"] = collection_source
        catalog["_id_str"] = str(catalog["_id"])

        # Añadir información adicional al catálogo
        if "created_at" in catalog and catalog["created_at"]:
            if isinstance(catalog["created_at"], str):
                catalog["created_at_formatted"] = catalog["created_at"]
            else:
                catalog["created_at_formatted"] = catalog["created_at"].strftime(
                    "%d/%m/%Y %H:%M"
                )
        else:
            catalog["created_at_formatted"] = "Fecha desconocida"

        # Contar filas según la estructura
        if "rows" in catalog and catalog["rows"] is not None:
            catalog["row_count"] = len(catalog["rows"])
            # Para compatibilidad con la plantilla
            catalog["data"] = catalog["rows"]
        elif "data" in catalog and catalog["data"] is not None:
            catalog["row_count"] = len(catalog["data"])
        else:
            catalog["row_count"] = 0
            catalog["data"] = []

        # Procesar las imágenes en cada fila
        from app.utils.s3_utils import get_s3_url

        # Verificar si hay datos en el catálogo
        if "data" in catalog and catalog["data"]:
            for row in catalog["data"]:
                # Procesar imágenes en el campo 'imagenes'
                if "imagenes" in row and row["imagenes"]:
                    # Crear un array con las URLs de las imágenes
                    row["imagen_urls"] = []
                    for img in row["imagenes"]:
                        if (
                            img and len(img) > 5
                        ):  # Verificar que el nombre de la imagen es válido
                            # Intentar obtener la URL de S3 primero
                            s3_url = get_s3_url(img)
                            if s3_url:
                                row["imagen_urls"].append(s3_url)
                                logger.debug(
                                    f"[ADMIN] Imagen S3 encontrada: {img} -> {s3_url}"
                                )
                            else:
                                # Si no está en S3, usar la URL local
                                local_url = url_for("static", filename=f"uploads/{img}")
                                row["imagen_urls"].append(local_url)
                                logger.debug(
                                    f"[ADMIN] Usando URL local para imagen: {img} -> {local_url}"
                                )

                    # Asignar las URLs procesadas a _imagenes para la plantilla
                    if "imagen_urls" in row:
                        row["_imagenes"] = row["imagen_urls"]

                # Procesar imágenes en el campo 'images' (compatibilidad)
                elif "images" in row and row["images"]:
                    # Crear un array con las URLs de las imágenes
                    row["imagen_urls"] = []
                    for img in row["images"]:
                        if (
                            img and len(img) > 5
                        ):  # Verificar que el nombre de la imagen es válido
                            # Intentar obtener la URL de S3 primero
                            s3_url = get_s3_url(img)
                            if s3_url:
                                row["imagen_urls"].append(s3_url)
                                logger.debug(
                                    f"[ADMIN] Imagen S3 encontrada: {img} -> {s3_url}"
                                )
                            else:
                                # Si no está en S3, usar la URL local
                                local_url = url_for("static", filename=f"uploads/{img}")
                                row["imagen_urls"].append(local_url)
                                logger.debug(
                                    f"[ADMIN] Usando URL local para imagen: {img} -> {local_url}"
                                )

                    # Para compatibilidad, copiar a 'imagenes'
                    row["imagenes"] = row["images"]

                # Asignar las URLs procesadas a _imagenes para la plantilla
                if "imagen_urls" in row:
                    row["_imagenes"] = row["imagen_urls"]

            logger.info(
                f"[ADMIN] Procesadas {catalog['row_count']} filas con imágenes para el catálogo {catalog_id}"
            )
        else:
            logger.warning(f"[ADMIN] El catálogo {catalog_id} no tiene filas o datos")

        logger.info(
            f"[ADMIN] Mostrando catálogo desde {collection_source}: {catalog.get('name', 'Sin nombre')}"
        )
        # Determinar return_url
        return_url = request.args.get("return_url") or request.referrer

        # Si el referrer es la página de edición de fila, construir una URL apropiada
        if return_url and "editar-fila" in return_url:
            # Intentar deducir el user_id para volver a la lista de catálogos del usuario
            user_id = None
            if "created_by_id" in catalog and catalog["created_by_id"]:
                user_id = str(catalog["created_by_id"])
            elif "created_by" in catalog and catalog["created_by"]:
                user = db.users.find_one(
                    {
                        "$or": [
                            {"email": catalog["created_by"]},
                            {"username": catalog["created_by"]},
                        ]
                    }
                )
                if user:
                    user_id = str(user["_id"])

            if user_id:
                return_url = url_for(
                    "admin.ver_catalogos_usuario_por_id", user_id=user_id
                )
            else:
                return_url = url_for("admin.dashboard_admin")
        elif not return_url:
            # Si no hay referrer, intentar deducir el user_id para volver a la lista de catálogos del usuario
            user_id = None
            if "created_by_id" in catalog and catalog["created_by_id"]:
                user_id = str(catalog["created_by_id"])
            elif "created_by" in catalog and catalog["created_by"]:
                user = db.users.find_one(
                    {
                        "$or": [
                            {"email": catalog["created_by"]},
                            {"username": catalog["created_by"]},
                        ]
                    }
                )
                if user:
                    user_id = str(user["_id"])

            if user_id:
                return_url = url_for(
                    "admin.ver_catalogos_usuario_por_id", user_id=user_id
                )
            else:
                return_url = url_for("admin.dashboard_admin")
        return render_template(
            "admin/ver_catalogo.html",
            catalog=catalog,
            error=None,
            collection_source=collection_source,
            return_url=return_url,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en ver_catalogo_unificado: {str(e)}", exc_info=True)
        flash(f"Error al cargar el catálogo: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route(
    "/catalogo/<collection_source>/<catalog_id>/editar", methods=["GET", "POST"]
)
@admin_required
def editar_catalogo_admin(collection_source: str, catalog_id: str):
    logger.info(
        f"[ADMIN] Entrando en editar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}"
    )
    try:
        db = get_mongo_db()
        if db is None:
            flash("Error: No se pudo acceder a la base de datos", "error")
            return redirect(url_for("admin.dashboard_admin"))
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            logger.warning(
                f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
            )
            flash("Catálogo no encontrado", "warning")
            return redirect(url_for("admin.dashboard_admin"))

        # Añadir información sobre la colección de origen
        catalog["collection_source"] = collection_source
        catalog["_id_str"] = str(catalog["_id"])

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description", "")
            headers_raw = request.form.get("headers")
            nueva_miniatura = request.form.get("miniatura", "").strip()

            # Manejar subida de archivo de miniatura
            miniatura_file = request.files.get("miniatura_file")
            if miniatura_file and miniatura_file.filename:
                try:
                    # Verificar que sea una imagen válida
                    if not miniatura_file.filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".webp")
                    ):
                        flash(
                            "El archivo debe ser una imagen (PNG, JPG, JPEG, GIF, WEBP).",
                            "error",
                        )
                        return render_template(
                            "admin/editar_catalogo.html", catalog=catalog
                        )

                    # Importar utilidades de imagen y S3
                    import uuid

                    from app.utils.image_utils import upload_image_to_s3

                    # Generar nombre único para el archivo
                    file_extension = miniatura_file.filename.split(".")[-1].lower()
                    unique_filename = f"miniatura_{uuid.uuid4().hex}.{file_extension}"

                    # Subir a S3
                    s3_url = upload_image_to_s3(miniatura_file, unique_filename)

                    if s3_url:
                        nueva_miniatura = s3_url
                        current_app.logger.info(f"Miniatura subida a S3: {s3_url}")
                    else:
                        # Fallback: guardar localmente si S3 falla
                        import os

                        from app.routes.catalogs_routes import get_upload_dir

                        upload_dir = get_upload_dir()
                        file_path = os.path.join(upload_dir, unique_filename)
                        miniatura_file.save(file_path)
                        nueva_miniatura = url_for(
                            "static", filename=f"uploads/{unique_filename}"
                        )
                        current_app.logger.info(
                            f"Miniatura guardada localmente: {nueva_miniatura}"
                        )

                except Exception as e:
                    current_app.logger.error(
                        f"Error al procesar archivo de miniatura: {str(e)}"
                    )
                    flash(f"Error al subir la imagen: {str(e)}", "error")
                    return render_template(
                        "admin/editar_catalogo.html", catalog=catalog
                    )

            update_data: Dict[str, Any] = {
                "name": name,
                "description": description,
                "updated_at": datetime.utcnow(),
            }
            if headers_raw is not None:
                headers = [h.strip() for h in headers_raw.split(",") if h.strip()]
                update_data["headers"] = headers

            # Añadir miniatura si se proporcionó
            if nueva_miniatura:
                update_data["miniatura"] = nueva_miniatura
            # Actualizar el catálogo en la colección correspondiente
            collection.update_one({"_id": ObjectId(catalog_id)}, {"$set": update_data})
            flash("Catálogo actualizado correctamente", "success")
            # Intentar obtener el ID del usuario para redirigir
            user_id = None
            if "created_by_id" in catalog and catalog["created_by_id"]:
                user_id = str(catalog["created_by_id"])
            elif "created_by" in catalog and catalog["created_by"]:
                # Buscar el usuario por email o username
                user = db.users.find_one(
                    {
                        "$or": [
                            {"email": catalog["created_by"]},
                            {"username": catalog["created_by"]},
                        ]
                    }
                )
                if user:
                    user_id = str(user["_id"])
            if user_id:
                return redirect(
                    url_for("admin.ver_catalogos_usuario_por_id", user_id=user_id)
                )
            else:
                return redirect(url_for("admin.dashboard_admin"))

        return render_template(
            "admin/editar_catalogo.html",
            catalog=catalog,
            collection_source=collection_source,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en editar_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al editar el catálogo: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route(
    "/catalogo/<collection_source>/<catalog_id>/editar-fila/<int:row_index>",
    methods=["GET", "POST"],
)
@admin_required
def editar_fila_admin(collection_source: str, catalog_id: str, row_index: int):
    """
    Editar una fila específica de un catálogo desde la interfaz de administración
    """
    logger.info(
        f"[ADMIN] Entrando en editar_fila_admin con collection_source={collection_source}, catalog_id={catalog_id}, row_index={row_index}"
    )
    try:
        db = get_mongo_db()
        if db is None:
            flash("Error: No se pudo acceder a la base de datos", "error")
            return redirect(url_for("admin.dashboard_admin"))

        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            logger.warning(
                f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
            )
            flash("Catálogo no encontrado", "warning")
            return redirect(url_for("admin.dashboard_admin"))

        # Asegurar que rows existe
        if "rows" not in catalog or not catalog["rows"]:
            catalog["rows"] = []

        # Verificar que el índice de fila es válido
        if row_index < 0 or row_index >= len(catalog["rows"]):
            flash("Índice de fila inválido", "error")
            return redirect(
                url_for(
                    "admin.ver_catalogo_unificado",
                    collection_source=collection_source,
                    catalog_id=catalog_id,
                )
            )

        row_data = catalog["rows"][row_index]

        # Añadir información sobre la colección de origen
        catalog["collection_source"] = collection_source
        catalog["_id_str"] = str(catalog["_id"])

        if request.method == "POST":
            # Procesar campos normales y especiales
            updated_row = {}
            for header in catalog["headers"]:
                if header == "Multimedia":
                    # Manejar campo Multimedia
                    multimedia_url = request.form.get(f"{header}_url", "").strip()
                    multimedia_file = request.files.get(f"{header}_file")

                    if multimedia_url:
                        updated_row[header] = multimedia_url
                    elif multimedia_file and multimedia_file.filename:
                        # Procesar archivo multimedia
                        import uuid  # noqa: I001
                        from werkzeug.utils import secure_filename
                        from app.routes.catalogs_routes import get_upload_dir

                        filename = secure_filename(
                            f"{uuid.uuid4().hex}_{multimedia_file.filename}"
                        )
                        upload_dir = get_upload_dir()
                        file_path = os.path.join(upload_dir, filename)
                        multimedia_file.save(file_path)
                        updated_row[header] = filename
                    else:
                        # Mantener valor existente si no hay cambios
                        updated_row[header] = row_data.get(header, "")

                elif header in ["Documentos", "Documentación"]:
                    # Manejar campo Documentos/Documentación
                    documento_url = request.form.get(f"{header}_url", "").strip()
                    documento_file = request.files.get(f"{header}_file")

                    if documento_url:
                        updated_row[header] = documento_url
                    elif documento_file and documento_file.filename:
                        # Procesar archivo documento
                        import uuid  # noqa: I001
                        from werkzeug.utils import secure_filename
                        from app.routes.catalogs_routes import get_upload_dir

                        filename = secure_filename(
                            f"{uuid.uuid4().hex}_{documento_file.filename}"
                        )
                        upload_dir = get_upload_dir()
                        file_path = os.path.join(upload_dir, filename)
                        documento_file.save(file_path)
                        updated_row[header] = filename
                    else:
                        # Mantener valor existente si no hay cambios
                        updated_row[header] = row_data.get(header, "")
                else:
                    # Campo normal
                    updated_row[header] = request.form.get(header, "")

            # Manejo de imágenes (mantener compatibilidad)
            if "images" in request.files:
                files = request.files.getlist("images")
                from app.routes.catalogs_routes import (
                    get_upload_dir,
                    allowed_image,
                )  # noqa: I001

                upload_dir = get_upload_dir()
                nuevas_imagenes = []
                for file in files:
                    if file and file.filename and allowed_image(file.filename):
                        import uuid  # noqa: I001
                        from werkzeug.utils import secure_filename

                        filename = secure_filename(
                            f"{uuid.uuid4().hex}_{file.filename}"
                        )
                        file_path = os.path.join(upload_dir, filename)
                        file.save(file_path)
                        nuevas_imagenes.append(filename)
                if nuevas_imagenes:
                    existing_images = updated_row.get("images", [])
                    if isinstance(existing_images, list):
                        updated_row["images"] = existing_images + nuevas_imagenes  # type: ignore
                    else:
                        updated_row["images"] = nuevas_imagenes  # type: ignore

            # Eliminar imágenes seleccionadas
            delete_images = request.form.getlist("delete_images")
            if delete_images:
                current_images = updated_row.get("images", [])
                if isinstance(current_images, list):
                    updated_row["images"] = [
                        img for img in current_images if img not in delete_images
                    ]  # type: ignore
                else:
                    updated_row["images"] = []  # type: ignore

            # Actualizar la fila en el catálogo
            catalog["rows"][row_index] = updated_row

            # Actualizar en la base de datos
            _ = collection.update_one(
                {"_id": ObjectId(catalog_id)}, {"$set": {"rows": catalog["rows"]}}
            )

            flash("Fila actualizada correctamente", "success")
            return redirect(
                url_for(
                    "admin.ver_catalogo_unificado",
                    collection_source=collection_source,
                    catalog_id=catalog_id,
                )
            )

        # Renderizar formulario de edición
        return render_template(
            "admin/editar_fila.html", catalog=catalog, row=row_data, row_index=row_index
        )

    except Exception as e:
        logger.error(f"Error en editar_fila_admin: {str(e)}", exc_info=True)
        flash(f"Error al editar la fila: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route("/admin/catalogo/<catalog_id>/get-images", methods=["GET"])
@admin_required
def get_catalog_images(catalog_id: str):
    """
    Obtiene las imágenes disponibles en un catálogo para la funcionalidad de miniatura automática
    """
    try:
        db = get_mongo_db()
        if db is None:
            return jsonify({"error": "No se pudo acceder a la base de datos"}), 500

        # Buscar en las colecciones principales
        catalog = None
        collections_to_check = ["spreadsheets", "catalogs"]

        for collection_name in collections_to_check:
            collection = db[collection_name]
            catalog = collection.find_one({"_id": ObjectId(catalog_id)})
            if catalog:
                break

        if not catalog:
            return jsonify({"error": "Catálogo no encontrado"}), 404

        # Extraer imágenes de las filas del catálogo
        images = []
        data_to_search = catalog.get("data", catalog.get("rows", []))

        for row in data_to_search:
            if isinstance(row, dict):
                # Buscar campos que contengan imágenes
                for _key, value in row.items():
                    if isinstance(value, str) and any(
                        ext in value.lower()
                        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", "http"]
                    ):
                        if value.startswith(("http://", "https://", "/")):
                            images.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and any(
                                ext in item.lower()
                                for ext in [
                                    ".jpg",
                                    ".jpeg",
                                    ".png",
                                    ".gif",
                                    ".webp",
                                    "http",
                                ]
                            ):
                                if item.startswith(("http://", "https://", "/")):
                                    images.append(item)

                # Buscar específicamente en campo 'imagenes' si existe
                if "imagenes" in row and isinstance(row["imagenes"], list):
                    for img in row["imagenes"]:
                        if isinstance(img, str) and img.startswith(
                            ("http://", "https://", "/")
                        ):
                            images.append(img)

        # Eliminar duplicados y limitar a 20 imágenes
        unique_images = list(dict.fromkeys(images))[:20]

        return jsonify({"images": unique_images})

    except Exception as e:
        current_app.logger.error(
            f"Error obteniendo imágenes del catálogo {catalog_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/catalogo/<collection_source>/<catalog_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_catalogo_admin(collection_source: str, catalog_id: str):
    try:
        logger.info(
            f"[ADMIN] Entrando en eliminar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}"
        )

        db = get_mongo_db()
        if db is None:
            flash("Error: No se pudo acceder a la base de datos", "error")
            return redirect(url_for("admin.dashboard_admin"))
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})

        if not catalog:
            logger.warning(
                f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
            )
            flash("Catálogo no encontrado", "warning")
            return redirect(url_for("admin.dashboard_admin"))

        # Eliminar el catálogo de la colección correspondiente
        result = collection.delete_one({"_id": ObjectId(catalog_id)})

        if result.deleted_count > 0:
            logger.info(
                f"[ADMIN] Catálogo eliminado correctamente: {catalog_id} de {collection_source}"
            )
            flash("Catálogo eliminado correctamente", "success")
        else:
            logger.warning(
                f"[ADMIN] No se pudo eliminar el catálogo: {catalog_id} de {collection_source}"
            )
            flash("No se pudo eliminar el catálogo", "warning")

        # Redirigir a la página anterior o al dashboard
        return redirect(request.referrer or url_for("admin.dashboard_admin"))
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en eliminar_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al eliminar el catálogo: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route("/catalogo/eliminar-multiple", methods=["POST"])
@admin_required
def eliminar_catalogos_multiple():
    """Elimina múltiples catálogos seleccionados."""
    try:
        logger.info("[ADMIN] Entrando en eliminar_catalogos_multiple")

        # Obtener los IDs de los catálogos a eliminar
        catalogos_data = request.json.get("catalogos", []) if request.json else []

        if not catalogos_data:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No se seleccionaron catálogos para eliminar",
                    }
                ),
                400,
            )

        db = get_mongo_db()
        if db is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Error: No se pudo acceder a la base de datos",
                    }
                ),
                500,
            )

        eliminados = []
        errores = []

        for catalogo_data in catalogos_data:
            try:
                collection_source = catalogo_data.get("collection_source")
                catalog_id = catalogo_data.get("catalog_id")

                if not collection_source or not catalog_id:
                    errores.append(f"ID o colección inválidos: {catalog_id}")
                    continue

                collection = db[collection_source]
                catalog = collection.find_one({"_id": ObjectId(catalog_id)})

                if not catalog:
                    errores.append(f"Catálogo no encontrado: {catalog_id}")
                    continue

                # Eliminar el catálogo
                result = collection.delete_one({"_id": ObjectId(catalog_id)})

                if result.deleted_count > 0:
                    eliminados.append(
                        {
                            "id": catalog_id,
                            "name": catalog.get("name", "Sin nombre"),
                            "collection": collection_source,
                        }
                    )
                    logger.info(
                        f"[ADMIN] Catálogo eliminado: {catalog_id} de {collection_source}"
                    )
                else:
                    errores.append(f"No se pudo eliminar: {catalog_id}")

            except Exception as e:
                error_msg = f"Error eliminando {catalog_id}: {str(e)}"
                errores.append(error_msg)
                logger.error(f"[ADMIN] {error_msg}")

        # Preparar respuesta
        response_data = {
            "success": True,
            "eliminados": eliminados,
            "total_eliminados": len(eliminados),
            "errores": errores,
            "total_errores": len(errores),
        }

        if eliminados:
            flash(f"Se eliminaron {len(eliminados)} catálogos correctamente", "success")
        if errores:
            flash(
                f"Errores en {len(errores)} catálogos: {', '.join(errores[:3])}",
                "warning",
            )

        return jsonify(response_data)

    except Exception as e:
        logger.error(
            f"[ADMIN] Error en eliminar_catalogos_multiple: {str(e)}", exc_info=True
        )
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500


@admin_bp.route("/db-scripts", methods=["GET", "POST"])
@admin_required
def db_scripts():
    """
    Maneja la ejecución de scripts de base de datos desde la interfaz de administración.

    Permite ejecutar scripts de mantenimiento de la base de datos con argumentos opcionales.
    Incluye medidas de seguridad para prevenir ejecución de comandos maliciosos.
    """
    import glob
    import shlex
    import subprocess
    import time
    from datetime import datetime

    # Configuración de directorios
    scripts_dir = os.path.join(os.getcwd(), "tools", "db_utils")

    # Lista de scripts permitidos (solo .py y que no empiecen con _)
    blacklist = {"__init__.py", "google_drive_utils.py"}
    scripts = []

    # Obtener información detallada de cada script
    for script_path in glob.glob(os.path.join(scripts_dir, "*.py")):
        script_name = os.path.basename(script_path)
        if script_name.startswith("_") or script_name in blacklist:
            continue

        # Obtener descripción del script (primera línea de comentario)
        description = "Sin descripción"
        try:
            with open(script_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") and "descripci" in line.lower():
                        description = line.lstrip("#").strip()
                        break
        except (OSError, PermissionError, UnicodeError) as e:
            description = f"Error al leer descripción: {str(e)}"

        scripts.append(
            {
                "name": script_name,
                "path": script_path,
                "description": description,
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(script_path)
                ).strftime("%Y-%m-%d %H:%M"),
            }
        )

    # Ordenar scripts por nombre
    scripts = sorted(scripts, key=lambda x: x["name"])

    # Variables para el formulario
    result = None
    error = None
    selected_script = None
    args = ""
    duration = None

    # Procesar envío del formulario
    if request.method == "POST":
        selected_script = request.form.get("script")
        args = request.form.get("args", "").strip()

        # Validar script seleccionado
        if not selected_script or not selected_script.endswith(".py"):
            error = "Script no válido."
        else:
            # Verificar que el script esté en la lista permitida
            script_info = next(
                (s for s in scripts if s["name"] == selected_script), None
            )
            if not script_info:
                error = "Script no permitido."
            else:
                # Construir comando de forma segura
                cmd = ["python3", script_info["path"]]

                # Validar y añadir argumentos
                if args:
                    try:
                        # Validar argumentos (solo permitir ciertos caracteres)
                        if not all(c.isalnum() or c in " -_=." for c in args):
                            raise ValueError(
                                "Caracteres no permitidos en los argumentos"
                            )

                        # Añadir argumentos de forma segura
                        cmd.extend(shlex.split(args))
                    except (ValueError, TypeError) as e:
                        error = f"Error en los argumentos: {str(e)}"

                # Ejecutar el script
                if not error:
                    start_time = time.time()
                    try:
                        # Ejecutar con timeout de 5 minutos
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=scripts_dir,  # Ejecutar desde el directorio del script
                        )

                        try:
                            out, err = proc.communicate(
                                timeout=300
                            )  # 5 minutos de timeout
                            duration = round(time.time() - start_time, 2)
                            result = out
                            error = err if err and err.strip() else None

                            # Registrar en log de auditoría
                            audit_log(
                                "db_script_execution",
                                user_id=session.get("user_id"),
                                details={
                                    "script": selected_script,
                                    "args": args,
                                    "duration_seconds": duration,
                                    "username": session.get("username", "desconocido"),
                                },
                            )

                            # Añadir mensaje de éxito
                            flash(
                                f"Script ejecutado correctamente en {duration} segundos.",
                                "success",
                            )

                        except subprocess.TimeoutExpired:
                            proc.kill()
                            error = "El script excedió el tiempo máximo de ejecución (5 minutos)"

                    except (OSError, PermissionError, TimeoutError) as e:
                        error = f"Error al ejecutar el script: {str(e)}"

    # Mensaje de advertencia de seguridad
    warning = (
        "⚠️ ADVERTENCIA: La ejecución de scripts puede afectar la base de datos. "
        "Asegúrate de entender lo que hace el script antes de ejecutarlo. "
        "Se recomienda probar en un entorno de desarrollo primero."
    )

    return render_template(
        "admin/db_scripts.html",
        scripts=scripts,
        result=result,
        error=error,
        selected_script=selected_script,
        args=args,
        duration=duration,
        warning=warning,
    )


@admin_bp.route("/db-status")
@admin_required
def db_status():
    """Muestra el estado de la conexión a MongoDB"""
    client = get_mongo_client()
    status = {
        "is_connected": False,
        "error": None,
        "databases": [],
        "collections": [],
        "server_info": None,
        "server_status": {},
    }

    try:
        if client is None:
            status["error"] = "Cliente MongoDB no disponible"
            return render_template("admin/db_status.html", status=status)
        # Probar conexión
        client.admin.command("ping")
        status["is_connected"] = True

        # Obtener información de la base de datos
        status["databases"] = client.list_database_names()

        # Obtener colecciones de la base de datos actual
        db = get_mongo_db()
        if db is not None:
            try:
                status["collections"] = db.list_collection_names()
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                current_app.logger.error(f"Error al obtener colecciones: {str(e)}")
                status["collections"] = []
                status["error"] = f"Error al obtener colecciones: {str(e)}"

        # Obtener información del servidor y convertir objetos no serializables
        def convert_timestamps(obj: Any) -> Any:
            from datetime import datetime

            from bson import Timestamp
            from bson.objectid import ObjectId

            if isinstance(obj, (list, tuple)):
                return [convert_timestamps(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, Timestamp):
                return {
                    "timestamp": obj.time,
                    "increment": obj.inc,
                    "as_datetime": datetime.fromtimestamp(obj.time).isoformat(),
                    "_type": "Timestamp",
                }
            elif isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, bytes):
                # Convertir bytes a string si es posible, o a una representación en base64
                try:
                    return obj.decode("utf-8")
                except UnicodeDecodeError:
                    import base64

                    return {
                        "_type": "bytes",
                        "base64": base64.b64encode(obj).decode("ascii"),
                        "length": len(obj),
                    }
            elif hasattr(obj, "isoformat"):  # Para objetos datetime
                return obj.isoformat()
            elif hasattr(obj, "items"):  # Para objetos tipo dict
                return {str(k): convert_timestamps(v) for k, v in obj.items()}
            elif hasattr(obj, "__dict__"):  # Para objetos con __dict__
                return convert_timestamps(obj.__dict__)
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                # Para cualquier otro tipo, devolver su representación como string
                return str(obj)

        # Obtener y procesar la información del servidor
        server_info = client.server_info()
        status["server_info"] = convert_timestamps(server_info)

        # Obtener y procesar estadísticas del servidor
        try:
            server_status = client.admin.command("serverStatus")
            status["server_status"] = convert_timestamps(server_status)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            status["server_status"] = {
                "error": f"No se pudo obtener el estado del servidor: {str(e)}"
            }

    except (
        ConnectionError,
        TimeoutError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        status["error"] = f"Error al conectar con MongoDB: {str(e)}"
        current_app.logger.error(
            f"Error en db_status: {str(e)}\n{traceback.format_exc()}"
        )
    return render_template("admin/db_status.html", status=status)


@admin_bp.route("/db/monitor")
@admin_required
def db_monitor():
    """Página de monitoreo en tiempo real de la base de datos"""
    client = get_mongo_client()
    status = {"is_connected": False, "error": None, "stats": {}, "server_status": {}}

    try:
        if client is None:
            status["error"] = "Cliente MongoDB no disponible"
            return render_template("admin/db_monitor.html", status=status)
        # Verificar conexión
        client.admin.command("ping")
        status["is_connected"] = True

        # Obtener estadísticas básicas
        db = get_mongo_db()
        if db is not None:
            try:
                status["stats"] = db.command("dbstats")
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                current_app.logger.error(
                    f"Error al obtener estadísticas de la base de datos: {str(e)}"
                )
                status["error"] = f"Error al obtener estadísticas: {str(e)}"

        # Obtener estado del servidor
        server_status = client.admin.command("serverStatus")
        status["server_status"] = server_status

        # Inicializar contadores de operaciones si no existen
        if "opcounters" not in session:
            session["opcounters"] = {
                "query": 0,
                "insert": 0,
                "update": 0,
                "delete": 0,
                "getmore": 0,
                "command": 0,
            }

        # Guardar timestamp de la última actualización
        session["last_update"] = time.time()

        # Obtener operaciones lentas (últimas 10)
        try:
            current_ops = client.admin.command("currentOp")
            if current_ops and "inprog" in current_ops:
                slow_ops = [
                    op
                    for op in current_ops["inprog"]
                    if op.get("secs_running", 0) > 1
                    and (
                        op.get("op") in ["query", "insert", "update", "remove"]
                        or "findAndModify" in str(op.get("command", {}))
                    )
                ]
                status["slow_ops"] = slow_ops[:10]
            else:
                status["slow_ops"] = []
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            current_app.logger.error(f"Error al obtener operaciones lentas: {str(e)}")
            status["slow_ops"] = []

    except (
        ConnectionError,
        TimeoutError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        status["error"] = f"Error al obtener estadísticas: {str(e)}"
        current_app.logger.error(
            f"Error en db_monitor: {str(e)}\n{traceback.format_exc()}"
        )

    return render_template("admin/db_monitor.html", status=status)


# Variables globales para el seguimiento de operaciones
last_ops: dict[str, int] = {}
last_update = time.time()


@admin_bp.route("/api/db/ops")
@admin_required
def get_db_ops():
    """
    Endpoint para obtener estadísticas de operaciones en tiempo real.
    Usa variables globales para el seguimiento entre solicitudes.
    """
    global last_ops, last_update

    try:
        client = get_mongo_client()
        if client is None:
            return (
                jsonify({"success": False, "error": "Cliente MongoDB no disponible"}),
                500,
            )
        server_status = client.admin.command("serverStatus")

        # Obtener contadores actuales
        current_ops = server_status.get("opcounters", {})
        current_time = time.time()

        # Calcular operaciones por segundo
        time_diff = current_time - last_update
        ops_per_sec = {}

        if last_ops and time_diff > 0:
            for op_type in [
                "query",
                "insert",
                "update",
                "delete",
                "getmore",
                "command",
            ]:
                if op_type in current_ops and op_type in last_ops:
                    ops_diff = current_ops[op_type] - last_ops[op_type]
                    ops_per_sec[op_type] = round(ops_diff / time_diff, 2)

        # Actualizar estado para la próxima solicitud
        last_ops = current_ops
        last_update = current_time

        # Obtener información de memoria
        memory = server_status.get("mem", {})

        # Obtener información de conexiones
        connections = server_status.get("connections", {})

        # Obtener operaciones lentas
        current_op = client.admin.current_op()
        slow_ops = []
        if "inprog" in current_op:
            for op in current_op["inprog"]:
                if (
                    "secs_running" in op and op["secs_running"] > 1
                ):  # Operaciones que llevan más de 1 segundo
                    slow_ops.append(
                        {
                            "opid": op.get("opid"),
                            "secs_running": op.get("secs_running"),
                            "op": op.get("op"),
                            "ns": op.get("ns"),
                            "client": op.get("client"),
                        }
                    )

        return jsonify(
            {
                "success": True,
                "ops_per_sec": ops_per_sec,
                "memory": memory,
                "connections": connections,
                "slow_ops": (
                    slow_ops[:10] if slow_ops else []
                ),  # Devolver solo las 10 operaciones más lentas
                "timestamp": current_time,
            }
        )

    except (
        ConnectionError,
        TimeoutError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        current_app.logger.error(f"Error en get_db_ops: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return (
            jsonify(
                {"success": False, "error": str(e), "traceback": traceback.format_exc()}
            ),
            500,
        )


def get_backup_dir() -> str:
    """Obtiene el directorio de respaldos, asegurando que exista"""
    # Usar la ruta absoluta basada en el directorio raíz del proyecto
    # El archivo está en app/routes/, necesitamos ir 3 niveles arriba para llegar a la raíz
    # app/routes/ -> app/ -> edf_catalogotablas/
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    backup_dir = os.path.join(project_root, "backups")

    # Log para depuración
    current_app.logger.info(f"Directorio de backup configurado: {backup_dir}")

    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


@admin_bp.route("/db/backup", methods=["GET", "POST"])
@admin_required
def db_backup():
    """Maneja la creación y gestión de respaldos"""
    backup_file = None  # Inicializar variable para evitar error de linter
    try:
        backup_dir = get_backup_dir()

        # Verificar permisos de escritura
        if not os.access(backup_dir, os.W_OK):
            raise Exception(f"No se tienen permisos de escritura en {backup_dir}")

        # Verificar espacio en disco (mínimo 1GB libre)
        disk_usage = shutil.disk_usage(backup_dir)
        if disk_usage.free < 1024**3:  # 1GB
            raise Exception(
                "Espacio en disco insuficiente (se requiere al menos 1GB libre)"
            )

        if request.method == "POST":
            try:
                # Intentar primero con mongodump (método tradicional)
                backup_created = False
                backup_file = None

                # Crear backup JSON directamente (método simplificado)
                try:
                    # Generar nombre de archivo con timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = os.path.join(
                        backup_dir, f"backup_{timestamp}.json.gz"
                    )

                    # Obtener datos de la base de datos
                    db = get_mongo_db()

                    # Crear estructura de backup
                    backup_data = {
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "version": "1.0",
                            "type": "json_backup",
                        },
                        "collections": {},
                    }

                    # Función para convertir objetos datetime a string
                    def convert_datetime(obj):
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        elif isinstance(obj, dict):
                            return {k: convert_datetime(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_datetime(item) for item in obj]
                        else:
                            return obj

                    # Obtener datos de las colecciones principales
                    collections_to_backup = ["catalogs", "users"]

                    for collection_name in collections_to_backup:
                        try:
                            collection = db[collection_name]
                            documents = list(collection.find({}))

                            # Convertir ObjectId y datetime para JSON serialization
                            converted_documents = []
                            for doc in documents:
                                # Crear una copia del documento
                                converted_doc = doc.copy()
                                if "_id" in converted_doc:
                                    converted_doc["_id"] = str(converted_doc["_id"])
                                # Convertir todos los campos datetime
                                converted_doc = convert_datetime(converted_doc)
                                converted_documents.append(converted_doc)

                            backup_data["collections"][
                                collection_name
                            ] = converted_documents
                            current_app.logger.info(
                                f"Colección {collection_name}: {len(documents)} documentos"
                            )

                        except Exception as e:
                            current_app.logger.warning(
                                f"Error al respaldar colección {collection_name}: {str(e)}"
                            )
                            backup_data["collections"][collection_name] = []

                    # Comprimir y escribir el backup
                    import gzip
                    import json

                    json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
                    compressed_data = gzip.compress(json_data.encode("utf-8"))

                    with open(backup_file, "wb") as f:
                        f.write(compressed_data)

                    backup_created = True
                    current_app.logger.info(
                        f"Backup JSON creado exitosamente: {backup_file}"
                    )
                    current_app.logger.info(
                        f"Tamaño del archivo: {len(compressed_data)} bytes"
                    )

                except Exception as backup_error:
                    current_app.logger.error(
                        f"Error al crear backup JSON: {str(backup_error)}"
                    )
                    raise Exception(
                        f"No se pudo crear el backup JSON: {str(backup_error)}"
                    ) from backup_error

                if not backup_created or not backup_file:
                    raise Exception("No se pudo crear el archivo de backup")

                audit_log(
                    "database_backup_created",
                    details={"filename": os.path.basename(backup_file)},
                )
                # Limpiar respaldos antiguos (mantener los 5 más recientes de cada tipo)
                try:
                    # Separar archivos por tipo
                    mongodb_backups = sorted(
                        [
                            f
                            for f in os.listdir(backup_dir)
                            if f.startswith("mongodb_backup_") and f.endswith(".gz")
                        ],
                        reverse=True,
                    )
                    json_backups = sorted(
                        [
                            f
                            for f in os.listdir(backup_dir)
                            if f.startswith("backup_")
                            and (f.endswith(".gz") or f.endswith(".json.gz"))
                        ],
                        reverse=True,
                    )

                    # Eliminar archivos binarios antiguos (mantener solo los 5 más recientes)
                    for old_backup in mongodb_backups[5:]:
                        try:
                            os.remove(os.path.join(backup_dir, old_backup))
                            current_app.logger.info(
                                f"Respaldo binario antiguo eliminado: {old_backup}"
                            )
                        except (OSError, PermissionError) as e:
                            current_app.logger.error(
                                f"Error al eliminar respaldo binario {old_backup}: {str(e)}"
                            )

                    # Eliminar archivos JSON antiguos (mantener solo los 5 más recientes)
                    for old_backup in json_backups[5:]:
                        try:
                            os.remove(os.path.join(backup_dir, old_backup))
                            current_app.logger.info(
                                f"Respaldo JSON antiguo eliminado: {old_backup}"
                            )
                        except (OSError, PermissionError) as e:
                            current_app.logger.error(
                                f"Error al eliminar respaldo JSON {old_backup}: {str(e)}"
                            )

                except (OSError, PermissionError) as e:
                    current_app.logger.error(
                        f"Error al limpiar respaldos antiguos: {str(e)}"
                    )
                    # No fallar la operación principal si falla la limpieza
                # Devolver JSON con URL de descarga
                download_url = url_for(
                    "admin.download_backup_alt", filename=os.path.basename(backup_file)
                )
                return jsonify({"status": "success", "download_url": download_url})
            except (OSError, PermissionError, ValueError, TypeError) as e:
                current_app.logger.error(
                    f"Error al crear respaldo: {str(e)}\n{traceback.format_exc()}"
                )
                # Intentar eliminar el archivo parcial si existe
                if backup_file and os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except Exception:
                        pass
                return jsonify({"status": "error", "message": str(e)}), 500
            # No continuar con render_template después de POST
            # (el frontend espera solo JSON)

        # Función auxiliar para obtener información de archivos
        def get_file_info(filepath: str) -> Dict[str, Any]:
            from collections import namedtuple

            FileInfo = namedtuple(
                "FileInfo", ["exists", "size", "mtime", "timestamp_from_name"]
            )

            try:
                current_app.logger.info(f"Obteniendo info de archivo: {filepath}")
                if not os.path.exists(filepath):
                    current_app.logger.warning(f"Archivo no existe: {filepath}")
                    file_info = FileInfo(False, 0, None, None)
                    return {
                        "exists": file_info.exists,
                        "size": file_info.size,
                        "mtime": file_info.mtime,
                        "timestamp_from_name": file_info.timestamp_from_name,
                    }

                stat = os.stat(filepath)

                # Extraer timestamp del nombre del archivo
                filename = os.path.basename(filepath)
                timestamp_from_name = None

                if filename.startswith("backup_") and "_" in filename:
                    try:
                        # backup_20250801_130738.json.gz -> 20250801_130738
                        # Usar split con maxsplit=1 para separar solo el primer _
                        parts = filename.split("_", 1)
                        if len(parts) >= 2:
                            # parts[1] = "20250801_130738.json.gz"
                            timestamp_part = parts[1].split(".")[0]  # "20250801_130738"
                            # Separar fecha y hora por el guión bajo
                            if "_" in timestamp_part:
                                date_time_parts = timestamp_part.split("_")
                                if len(date_time_parts) == 2:
                                    date_part = date_time_parts[0]  # "20250801"
                                    time_part = date_time_parts[1]  # "130738"

                                    if (
                                        len(date_part) == 8 and len(time_part) == 6
                                    ):  # YYYYMMDD y HHMMSS
                                        year = int(date_part[:4])
                                        month = int(date_part[4:6])
                                        day = int(date_part[6:8])
                                        hour = int(time_part[:2])
                                        minute = int(time_part[2:4])
                                        second = int(time_part[4:6])

                                        # Crear datetime usando la hora local (como se generó originalmente)
                                        timestamp_from_name = datetime(
                                            year, month, day, hour, minute, second
                                        )
                                        current_app.logger.info(
                                            f"Timestamp extraído del nombre: {timestamp_from_name}"
                                        )
                    except (ValueError, IndexError) as e:
                        current_app.logger.warning(
                            f"No se pudo extraer timestamp del nombre {filename}: {str(e)}"
                        )
                        timestamp_from_name = None

                file_info = FileInfo(
                    exists=True,
                    size=stat.st_size,
                    mtime=datetime.fromtimestamp(stat.st_mtime),
                    timestamp_from_name=timestamp_from_name,
                )
                current_app.logger.info(
                    f"Info de archivo obtenida: {filepath} - Tamaño: {file_info.size}, Modificado: {file_info.mtime}, Timestamp nombre: {file_info.timestamp_from_name}"
                )
                return {
                    "exists": file_info.exists,
                    "size": file_info.size,
                    "mtime": file_info.mtime,
                    "timestamp_from_name": file_info.timestamp_from_name,
                }
            except (OSError, PermissionError) as e:
                current_app.logger.error(
                    f"Error al obtener info de archivo {filepath}: {str(e)}"
                )
                file_info = FileInfo(False, 0, None, None)
                return {
                    "exists": file_info.exists,
                    "size": file_info.size,
                    "mtime": file_info.mtime,
                    "timestamp_from_name": file_info.timestamp_from_name,
                }

        # Listar respaldos existentes usando get_backup_files
        backups = []
        try:
            backup_files_info = get_backup_files(backup_dir)
            current_app.logger.info(
                f"Archivos de backup encontrados: {len(backup_files_info)}"
            )

            # Enviar todos los backups para que DataTables maneje la paginación
            backups = backup_files_info
            total_backups = len(backup_files_info)

            current_app.logger.info(
                f"Enviando todos los {total_backups} archivos de backup para paginación del lado del cliente"
            )

        except Exception as e:
            current_app.logger.error(f"Error al listar respaldos: {str(e)}")
            flash("Error al listar los respaldos existentes", "error")
            total_backups = 0

        # Obtener el conteo de respaldos en Google Drive
        drive_backups_count = 0
        try:
            db = get_mongo_db()
            if db is not None:
                drive_backups_count = db.backups.count_documents({})
            else:
                drive_backups_count = 0
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            current_app.logger.error(f"Error al contar respaldos en Drive: {str(e)}")
            drive_backups_count = 0

        # Solo renderizar plantilla en GET
        current_app.logger.info(f"Renderizando template con {len(backups)} backups")
        current_app.logger.info(f"Backup dir: {backup_dir}")
        current_app.logger.info(f"Drive backups count: {drive_backups_count}")

        return render_template(
            "admin/db_backup.html",
            backups=backups,
            backup_dir=backup_dir,
            get_file_info=get_file_info,
            drive_backups_count=drive_backups_count,
            # Parámetros de paginación (ahora manejados por DataTables)
            total_backups=total_backups,
        )

    except (
        OSError,
        PermissionError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        current_app.logger.error(
            f"Error en db_backup: {str(e)}\n{traceback.format_exc()}"
        )
        flash(f"Error en la operación de respaldo: {str(e)}", "error")
        return render_template(
            "admin/db_backup.html",
            backups=[],
            backup_dir=get_backup_dir(),
            get_file_info=lambda x: type(
                "FileInfo",
                (),
                {
                    "exists": False,
                    "size": 0,
                    "mtime": None,
                    "timestamp_from_name": None,
                },
            )(),
            drive_backups_count=0,
            # Parámetros de paginación por defecto
            total_backups=0,
        )


@admin_bp.route("/db/performance", methods=["GET", "POST"])
@admin_required
def db_performance():
    """Ejecuta y muestra pruebas de rendimiento"""
    results = None

    if request.method == "POST":
        try:
            # Obtener parámetros del formulario
            num_ops = int(request.form.get("num_ops", 100))
            batch_size = int(request.form.get("batch_size", 10))

            # Ejecutar pruebas de rendimiento
            db = get_mongo_db()
            if db is None:
                results = {
                    "status": "error",
                    "message": "No se pudo acceder a la base de datos",
                }
                return render_template("admin/db_performance.html", results=results)
            test_collection = db.performance_test

            # Limpiar colección de prueba
            test_collection.drop()

            # Prueba de inserción
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                batch = [
                    {"value": j, "timestamp": datetime.utcnow()}
                    for j in range(i, min(i + batch_size, num_ops))
                ]
                test_collection.insert_many(batch)
            insert_time = time.time() - start_time

            # Prueba de consulta
            start_time = time.time()
            for _ in range(num_ops):
                list(test_collection.find().limit(10))
            query_time = time.time() - start_time

            # Prueba de actualización
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                test_collection.update_many(
                    {
                        "_id": {
                            "$in": [
                                doc["_id"]
                                for doc in test_collection.find()
                                .skip(i)
                                .limit(batch_size)
                            ]
                        }
                    },
                    {"$set": {"updated": True}},
                )
            update_time = time.time() - start_time

            # Limpiar
            test_collection.drop()

            # Crear métricas con los resultados
            insert_metrics = {
                "time": insert_time,
                "ops_sec": num_ops / insert_time if insert_time > 0 else 0,
            }
            query_metrics = {
                "time": query_time,
                "ops_sec": num_ops / query_time if query_time > 0 else 0,
            }
            update_metrics = {
                "time": update_time,
                "ops_sec": num_ops / update_time if update_time > 0 else 0,
            }

            # Estructurar los resultados según lo esperado por la plantilla
            results = {
                "status": "success",
                "operations": num_ops,
                "batch_size": batch_size,
                "metrics": {
                    "insert": insert_metrics,
                    "query": query_metrics,
                    "update": update_metrics,
                },
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            results = {
                "status": "error",
                "message": f"Error al ejecutar pruebas: {str(e)}",
                "traceback": traceback.format_exc(),
            }
            current_app.logger.error(
                f"Error en db_performance: {str(e)}\n{results['traceback']}"
            )

    return render_template("admin/db_performance.html", results=results)


# Definir el blueprint con el prefijo de URL correcto
# Cambiamos el nombre a 'admin' para que coincida con el prefijo
admin_logs_bp = Blueprint("admin_logs", __name__)

# Decorador para restringir acceso solo a admin (importamos el decorador principal)

LOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../logs/flask_debug.log")
)


@admin_logs_bp.route("/logs")
@admin_required_logs
def logs_manual():
    return render_template("admin/logs_manual.html")


@admin_logs_bp.route("/logs/tail")
@admin_required_logs
def logs_tail():
    import os
    from datetime import datetime

    # Obtener parámetros
    n = int(request.args.get("n", 20))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    keyword = request.args.get("keyword", "").strip()
    log_file = request.args.get("log_file", "flask_debug.log")

    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)

    if not os.path.isfile(log_path):
        return (
            jsonify(
                {
                    "logs": [f"Archivo no encontrado: {log_file}\n"],
                    "error": "Archivo no encontrado",
                }
            ),
            404,
        )

    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Aplicar filtros combinados
        filtered_lines = []
        date_format = "%Y-%m-%d"

        # Preparar filtros de fecha
        date_from_obj = None
        date_to_obj = None
        if date_from:
            date_from_obj = datetime.strptime(date_from, date_format).date()
        if date_to:
            date_to_obj = datetime.strptime(date_to, date_format).date()

        for line in lines:
            # Aplicar filtro de palabra clave
            if keyword and keyword.lower() not in line.lower():
                continue

            # Aplicar filtros de fecha
            if date_from_obj or date_to_obj:
                # Extraer la fecha del log (asumiendo formato de fecha al inicio de la línea)
                log_date_str = " ".join(
                    line.split()[:2]
                )  # Toma los dos primeros segmentos (fecha y hora)
                try:
                    log_datetime = datetime.strptime(
                        log_date_str, "%Y-%m-%d %H:%M:%S,%f"
                    )
                    log_date = log_datetime.date()

                    # Aplicar filtros de fecha
                    if date_from_obj and log_date < date_from_obj:
                        continue
                    if date_to_obj and log_date > date_to_obj:
                        continue

                    filtered_lines.append(line)
                except ValueError:
                    # Si no se puede extraer la fecha, incluir la línea por defecto
                    filtered_lines.append(line)
            else:
                # Si no hay filtro de fechas, solo aplicar filtro de palabra clave
                filtered_lines.append(line)

        # Aplicar límite de líneas si se especificó
        result_lines = filtered_lines[-n:] if n > 0 else filtered_lines

        return jsonify(
            {
                "logs": result_lines,
                "total_lines": len(lines),
                "filtered_lines": len(result_lines),
            }
        )

    except (OSError, PermissionError, UnicodeError) as e:
        return (
            jsonify(
                {
                    "logs": [f"Error al leer el archivo de log: {str(e)}\n"],
                    "error": str(e),
                }
            ),
            500,
        )


@admin_logs_bp.route("/logs/search")
@admin_required_logs
def logs_search():
    import os

    kw = request.args.get("kw", "").strip()
    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        from flask import abort

        abort(404, description=f"Archivo no encontrado: {log_file}")
    if not kw:
        return jsonify({"logs": []})  # Esto es éxito, no error, se mantiene igual.
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        lines = [line for line in f if kw.lower() in line.lower()]
    return jsonify({"logs": lines})


@admin_logs_bp.route("/logs/download")
@admin_required_logs
def logs_download():
    import os

    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return "Archivo no encontrado", 404
    return send_file(log_path, as_attachment=True, download_name=log_file)


@admin_logs_bp.route("/logs/clear", methods=["POST"])
@admin_required_logs
def logs_clear():
    import os
    from datetime import datetime

    log_file = request.args.get("log_file", "flask_debug.log")
    lines = request.form.get("lines")
    date = request.form.get("date")

    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)

    if not os.path.isfile(log_path):
        return jsonify({"status": f"Archivo no encontrado: {log_file}"}), 404

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        if not all_lines:
            return jsonify({"status": f"Log {log_file} ya está vacío"}), 200

        lines_to_keep = []

        if lines:
            # Truncar por número de líneas
            try:
                num_lines = int(lines)
                if num_lines > 0:
                    lines_to_keep = all_lines[-num_lines:]
                else:
                    lines_to_keep = []
            except ValueError:
                return jsonify({"status": "Número de líneas inválido"}), 400

        elif date:
            # Truncar por fecha
            try:
                cutoff_date = datetime.strptime(date, "%Y-%m-%d").date()
                lines_to_keep = []

                for line in all_lines:
                    # Extraer la fecha del log (asumiendo formato de fecha al inicio de la línea)
                    log_date_str = " ".join(line.split()[:2])
                    try:
                        log_datetime = datetime.strptime(
                            log_date_str, "%Y-%m-%d %H:%M:%S,%f"
                        )
                        log_date = log_datetime.date()

                        # Mantener líneas desde la fecha de corte en adelante
                        if log_date >= cutoff_date:
                            lines_to_keep.append(line)
                    except ValueError:
                        # Si no se puede extraer la fecha, mantener la línea por defecto
                        lines_to_keep.append(line)

            except ValueError:
                return (
                    jsonify({"status": "Formato de fecha inválido. Use YYYY-MM-DD"}),
                    400,
                )
        else:
            # Si no se especifican parámetros, limpiar todo
            lines_to_keep = []

        # Escribir las líneas que se van a mantener
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(lines_to_keep)

        lines_removed = len(all_lines) - len(lines_to_keep)

        if lines:
            status_msg = f"Log {log_file} truncado: se mantuvieron las últimas {len(lines_to_keep)} líneas"
        elif date:
            status_msg = f"Log {log_file} truncado: se mantuvieron {len(lines_to_keep)} líneas desde {date}"
        else:
            status_msg = f"Log {log_file} limpiado completamente"

        return (
            jsonify(
                {
                    "status": status_msg,
                    "lines_removed": lines_removed,
                    "lines_kept": len(lines_to_keep),
                }
            ),
            200,
        )

    except (OSError, PermissionError, UnicodeError) as e:
        return jsonify({"status": f"Error al procesar el archivo: {str(e)}"}), 500


@admin_logs_bp.route("/logs/size")
@admin_required_logs
def logs_size():
    import os

    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return jsonify({"size": 0, "backups": 0, "error": "Archivo no encontrado"}), 404
    size = os.path.getsize(log_path)
    backups = len([f for f in os.listdir(logs_dir) if f.startswith(log_file + ".")])
    return jsonify({"size": size, "backups": backups})


@admin_bp.route("/backups/list", methods=["GET", "POST"])
@admin_required
def backups_list():
    backups_dir = os.path.join(os.getcwd(), "backups")
    backup_files = get_backup_files(backups_dir)
    if request.method == "POST":
        # Borrado individual
        filename = request.form.get("filename")
        if filename and ".." not in filename and "/" not in filename:
            file_path = os.path.join(backups_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    flash(f"Backup {filename} eliminado correctamente", "success")
                    audit_log(
                        "backup_file_deleted_manually",
                        user_id=session.get("user_id"),
                        details={
                            "filename": filename,
                            "username": session.get("username", "desconocido"),
                        },
                    )
                except (OSError, PermissionError) as e:
                    flash(f"Error al eliminar el backup: {str(e)}", "danger")
            else:
                flash("El archivo no existe", "warning")
        else:
            flash("Nombre de archivo no válido", "danger")
        return redirect(url_for("admin.backups_list"))
    return render_template("admin/backups_list.html", backup_files=backup_files)


@admin_bp.route("/backups/download/<filename>")
@admin_required
def download_backup(filename: str):
    backups_dir = os.path.join(os.getcwd(), "backups")
    if ".." in filename or "/" in filename:
        flash("Nombre de archivo no válido", "danger")
        return redirect(url_for("admin.backups_list"))
    file_path = os.path.join(backups_dir, filename)
    if not os.path.exists(file_path):
        flash("El archivo no existe", "warning")
        return redirect(url_for("admin.backups_list"))
    audit_log(
        "backup_file_download",
        user_id=session.get("user_id"),
        details={
            "filename": filename,
            "username": session.get("username", "desconocido"),
        },
    )
    return send_file(file_path, as_attachment=True, download_name=filename)


@admin_bp.route("/db/backup/download/<filename>")
@admin_required
def download_backup_alt(filename: str):
    """Descarga un archivo de respaldo (ruta alternativa para db_backup)"""
    try:
        backup_dir = get_backup_dir()
        file_path = os.path.join(backup_dir, filename)

        if not os.path.exists(file_path):
            return (
                jsonify(
                    {"status": "error", "message": "El archivo de respaldo no existe"}
                ),
                404,
            )

        audit_log(
            "backup_file_download",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "username": session.get("username", "desconocido"),
            },
        )
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error al descargar backup {filename}: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error al descargar el archivo: {str(e)}",
                }
            ),
            500,
        )


@admin_bp.route("/restore-local-backup", methods=["POST"])
@admin_required
def restore_local_backup():
    """Restaura un backup local desde el directorio de backups"""
    try:
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return (
                jsonify({"success": False, "error": "Falta el parámetro filename"}),
                400,
            )

        current_app.logger.info(
            f"Iniciando restauración desde backup local: {filename}"
        )

        # Importar las utilidades necesarias
        import gzip
        import json
        import tempfile

        from bson import ObjectId

        # Obtener la ruta del archivo de backup
        backup_dir = get_backup_dir()
        file_path = os.path.join(backup_dir, filename)

        if not os.path.exists(file_path):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"El archivo de backup {filename} no existe",
                    }
                ),
                404,
            )

        current_app.logger.info(f"Procesando archivo local: {file_path}")

        # Verificar el tipo de archivo basándose en el nombre
        if filename.startswith("mongodb_backup_"):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Este archivo es un backup binario de MongoDB (mongodump). Solo se pueden restaurar backups en formato JSON. Use el archivo backup_*.json.gz en su lugar.",
                    }
                ),
                400,
            )

        # Determinar el formato del archivo y procesarlo
        backup_data = None

        # Verificar si el archivo es GZIP comprimido
        try:
            with open(file_path, "rb") as f:
                # Leer los primeros bytes para detectar el formato
                magic_bytes = f.read(2)
                f.seek(0)  # Volver al inicio

                if magic_bytes.startswith(b"\x1f\x8b"):  # GZIP magic bytes
                    current_app.logger.info("Archivo detectado como GZIP comprimido")
                    try:
                        with gzip.open(file_path, "rb") as gz_file:
                            compressed_content = gz_file.read()
                            current_app.logger.info(
                                f"Contenido GZIP descomprimido, longitud: {len(compressed_content)} bytes"
                            )

                            # Intentar decodificar como UTF-8
                            try:
                                content = compressed_content.decode("utf-8")
                                current_app.logger.info(
                                    f"Contenido decodificado como UTF-8, longitud: {len(content)} caracteres"
                                )
                            except UnicodeDecodeError as decode_error:
                                current_app.logger.error(
                                    f"Error decodificando UTF-8: {str(decode_error)}"
                                )
                                # Intentar con otras codificaciones
                                try:
                                    content = compressed_content.decode("latin-1")
                                    current_app.logger.info(
                                        f"Contenido decodificado como latin-1, longitud: {len(content)} caracteres"
                                    )
                                except UnicodeDecodeError:
                                    return (
                                        jsonify(
                                            {
                                                "success": False,
                                                "error": "No se pudo decodificar el contenido del archivo comprimido",
                                            }
                                        ),
                                        400,
                                    )

                            # Intentar parsear como JSON
                            try:
                                backup_data = json.loads(content)
                                current_app.logger.info(
                                    f"JSON parseado exitosamente, tipo: {type(backup_data)}"
                                )
                            except json.JSONDecodeError as e:
                                current_app.logger.error(
                                    f"Error parseando JSON: {str(e)}"
                                )
                                current_app.logger.error(
                                    f"Primeros 200 caracteres del contenido: {content[:200]}"
                                )

                                # Verificar si es un archivo de backup de MongoDB binario
                                if (
                                    content.startswith("BSON")
                                    or "mongodump" in content.lower()
                                    or "concurrent_collections" in content
                                    or "server_version" in content
                                ):
                                    return (
                                        jsonify(
                                            {
                                                "success": False,
                                                "error": "Este archivo es un backup binario de MongoDB (mongodump). Solo se pueden restaurar backups en formato JSON. Use el archivo backup_*.json.gz en su lugar.",
                                            }
                                        ),
                                        400,
                                    )

                                return (
                                    jsonify(
                                        {
                                            "success": False,
                                            "error": f"El archivo de backup no contiene JSON válido. Error: {str(e)}",
                                        }
                                    ),
                                    400,
                                )

                    except Exception as gzip_error:
                        current_app.logger.error(
                            f"Error procesando GZIP: {str(gzip_error)}"
                        )
                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "error": f"Error al descomprimir el archivo GZIP: {str(gzip_error)}",
                                }
                            ),
                            400,
                        )
                else:
                    current_app.logger.info("Archivo detectado como texto plano")
                    # Intentar como archivo de texto plano
                    try:
                        with open(file_path, encoding="utf-8") as file:
                            content = file.read()
                            current_app.logger.info(
                                f"Contenido plano leído, longitud: {len(content)} caracteres"
                            )
                            backup_data = json.loads(content)
                            current_app.logger.info(
                                f"JSON plano parseado exitosamente, tipo: {type(backup_data)}"
                            )
                    except UnicodeDecodeError as decode_error:
                        current_app.logger.error(
                            f"Error decodificando UTF-8: {str(decode_error)}"
                        )
                        # Intentar con otras codificaciones
                        try:
                            with open(file_path, encoding="latin-1") as file:
                                content = file.read()
                                current_app.logger.info(
                                    f"Contenido plano leído como latin-1, longitud: {len(content)} caracteres"
                                )
                                backup_data = json.loads(content)
                                current_app.logger.info(
                                    f"JSON plano parseado exitosamente, tipo: {type(backup_data)}"
                                )
                        except (UnicodeDecodeError, json.JSONDecodeError) as e:
                            current_app.logger.error(
                                f"Error procesando archivo plano: {str(e)}"
                            )
                            return (
                                jsonify(
                                    {
                                        "success": False,
                                        "error": f"Formato de archivo no válido: {str(e)}",
                                    }
                                ),
                                400,
                            )
                    except json.JSONDecodeError as e:
                        current_app.logger.error(
                            f"Error parseando JSON plano: {str(e)}"
                        )
                        current_app.logger.error(
                            f"Primeros 200 caracteres del contenido: {content[:200]}"
                        )

                        # Verificar si es un archivo de backup de MongoDB binario
                        if (
                            content.startswith("BSON")
                            or "mongodump" in content.lower()
                            or "concurrent_collections" in content
                            or "server_version" in content
                        ):
                            return (
                                jsonify(
                                    {
                                        "success": False,
                                        "error": "Este archivo es un backup binario de MongoDB (mongodump). Solo se pueden restaurar backups en formato JSON. Use el archivo backup_*.json.gz en su lugar.",
                                    }
                                ),
                                400,
                            )

                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "error": f"Formato de archivo no válido. Error JSON: {str(e)}",
                                }
                            ),
                            400,
                        )

        except Exception as e:
            current_app.logger.error(f"Error general procesando archivo: {str(e)}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Error al procesar el archivo: {str(e)}",
                    }
                ),
                400,
            )

        if not backup_data:
            current_app.logger.error("No se pudo procesar el contenido del backup")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo procesar el contenido del backup",
                    }
                ),
                400,
            )

        current_app.logger.info(f"Backup data procesado, tipo: {type(backup_data)}")

        # Validar estructura del backup
        if isinstance(backup_data, dict):
            # Estructura nueva con metadata y collections
            current_app.logger.info("Backup detectado como estructura con metadata")
            if (
                "collections" in backup_data
                and "catalogs" in backup_data["collections"]
            ):
                backup_data = backup_data["collections"]["catalogs"]
                current_app.logger.info(
                    f"Extraídos {len(backup_data)} documentos de la colección 'catalogs'"
                )
            else:
                current_app.logger.error(
                    "Backup no contiene la estructura esperada (collections.catalogs)"
                )
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "El backup no contiene la estructura esperada",
                        }
                    ),
                    400,
                )
        elif not isinstance(backup_data, list):
            current_app.logger.error(
                f"Backup no es una lista ni un diccionario válido, es: {type(backup_data)}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "El backup debe contener una lista de documentos o una estructura válida",
                    }
                ),
                400,
            )

        current_app.logger.info(f"Backup contiene {len(backup_data)} documentos")

        # Obtener la colección de catálogos
        catalog_collection = get_catalogs_collection()
        if catalog_collection is None:
            return (
                jsonify(
                    {"success": False, "error": "No se pudo acceder a la base de datos"}
                ),
                500,
            )

        # Procesar los documentos para restaurar ObjectIds
        processed_docs = []
        for doc in backup_data:
            if isinstance(doc, dict):
                # Convertir _id string de vuelta a ObjectId si es necesario
                if "_id" in doc and isinstance(doc["_id"], str):
                    try:
                        doc["_id"] = ObjectId(doc["_id"])
                    except Exception:
                        # Si no se puede convertir, generar nuevo ObjectId
                        doc["_id"] = ObjectId()
                processed_docs.append(doc)

        if not processed_docs:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se encontraron documentos válidos en el backup",
                    }
                ),
                400,
            )

        # Limpiar la colección actual (CUIDADO: esto elimina todos los datos)
        current_app.logger.warning(
            "Eliminando todos los documentos de la colección antes de restaurar"
        )
        delete_result = catalog_collection.delete_many({})
        current_app.logger.info(f"Documentos eliminados: {delete_result.deleted_count}")

        # Insertar los documentos restaurados
        insert_result = catalog_collection.insert_many(processed_docs)
        inserted_count = len(insert_result.inserted_ids)

        # Registrar en auditoría
        audit_log(
            "database_restore_from_local",
            user_id=session.get("user_id"),
            details={
                "filename": filename,
                "documents_restored": inserted_count,
                "documents_deleted": delete_result.deleted_count,
                "username": session.get("username", "desconocido"),
            },
        )

        current_app.logger.info(
            f"Restauración completada: {inserted_count} documentos insertados"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Backup restaurado exitosamente. {inserted_count} documentos restaurados.",
                "documents_restored": inserted_count,
                "documents_deleted": delete_result.deleted_count,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error en restore_local_backup: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return (
            jsonify(
                {"success": False, "error": f"Error interno del servidor: {str(e)}"}
            ),
            500,
        )


@admin_bp.route("/restore-drive-backup", methods=["POST"])
@admin_required
def restore_drive_backup():
    try:
        backup_id = request.form.get("backup_id")
        download_url = request.form.get("download_url")

        if not backup_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Falta el parámetro requerido (backup_id)",
                    }
                ),
                400,
            )

        current_app.logger.info(
            f"Iniciando restauración desde Google Drive: {backup_id}"
        )

        # Importar las utilidades necesarias
        import gzip
        import json
        import tempfile

        from bson import ObjectId

        # Descargar el archivo desde Google Drive usando la API
        from tools.db_utils.google_drive_utils import download_file

        # Obtener el file_id del backup_id (que es el mismo en este caso)
        file_id = backup_id

        # Descargar el archivo usando la API de Google Drive
        file_content = download_file(file_id)

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".gz", mode="wb"
        ) as temp_file:
            # Asegurar que file_content sea bytes
            if isinstance(file_content, str):
                file_content = file_content.encode("utf-8")
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            # Determinar el formato del archivo y procesarlo
            backup_data = None

            current_app.logger.info(f"Procesando archivo temporal: {temp_path}")

            # Intentar como archivo GZIP primero
            try:
                with gzip.open(temp_path, "rt", encoding="utf-8") as gz_file:
                    content = gz_file.read()
                    current_app.logger.info(
                        f"Contenido GZIP leído, longitud: {len(content)} caracteres"
                    )
                    # Intentar parsear como JSON
                    try:
                        backup_data = json.loads(content)
                        current_app.logger.info(
                            f"JSON parseado exitosamente, tipo: {type(backup_data)}"
                        )
                    except json.JSONDecodeError as e:
                        # Si no es JSON válido, asumir que es un dump de MongoDB
                        current_app.logger.error(f"Error parseando JSON: {str(e)}")
                        current_app.logger.info(
                            "Archivo detectado como dump de MongoDB"
                        )
                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "error": "Los dumps de MongoDB (.gz) no son compatibles con esta función. Use mongorestore manualmente.",
                                }
                            ),
                            400,
                        )
            except (gzip.BadGzipFile, OSError) as e:
                current_app.logger.error(f"Error leyendo GZIP: {str(e)}")
                # Si no es GZIP, intentar como JSON plano
                try:
                    with open(temp_path, encoding="utf-8") as file:
                        content = file.read()
                        current_app.logger.info(
                            f"Contenido plano leído, longitud: {len(content)} caracteres"
                        )
                        backup_data = json.load(file)
                        current_app.logger.info(
                            f"JSON plano parseado exitosamente, tipo: {type(backup_data)}"
                        )
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Error parseando JSON plano: {str(e)}")
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"Formato de archivo no válido: {str(e)}",
                            }
                        ),
                        400,
                    )

            if not backup_data:
                current_app.logger.error("No se pudo procesar el contenido del backup")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "No se pudo procesar el contenido del backup",
                        }
                    ),
                    400,
                )

            current_app.logger.info(f"Backup data procesado, tipo: {type(backup_data)}")

            # Validar estructura del backup
            if isinstance(backup_data, dict):
                # Estructura nueva con metadata y collections
                current_app.logger.info("Backup detectado como estructura con metadata")
                if (
                    "collections" in backup_data
                    and "catalogs" in backup_data["collections"]
                ):
                    backup_data = backup_data["collections"]["catalogs"]
                    current_app.logger.info(
                        f"Extraídos {len(backup_data)} documentos de la colección 'catalogs'"
                    )
                else:
                    current_app.logger.error(
                        "Backup no contiene la estructura esperada (collections.catalogs)"
                    )
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "El backup no contiene la estructura esperada",
                            }
                        ),
                        400,
                    )
            elif not isinstance(backup_data, list):
                current_app.logger.error(
                    f"Backup no es una lista ni un diccionario válido, es: {type(backup_data)}"
                )
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "El backup debe contener una lista de documentos o una estructura válida",
                        }
                    ),
                    400,
                )

            current_app.logger.info(f"Backup contiene {len(backup_data)} documentos")

            # Obtener la colección de catálogos
            catalog_collection = get_catalogs_collection()
            if catalog_collection is None:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "No se pudo acceder a la base de datos",
                        }
                    ),
                    500,
                )

            # Procesar los documentos para restaurar ObjectIds
            processed_docs = []
            for doc in backup_data:
                if isinstance(doc, dict):
                    # Convertir _id string de vuelta a ObjectId si es necesario
                    if "_id" in doc and isinstance(doc["_id"], str):
                        try:
                            doc["_id"] = ObjectId(doc["_id"])
                        except Exception:
                            # Si no se puede convertir, generar nuevo ObjectId
                            doc["_id"] = ObjectId()
                    processed_docs.append(doc)

            if not processed_docs:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "No se encontraron documentos válidos en el backup",
                        }
                    ),
                    400,
                )

            # Limpiar la colección actual (CUIDADO: esto elimina todos los datos)
            current_app.logger.warning(
                "Eliminando todos los documentos de la colección antes de restaurar"
            )
            delete_result = catalog_collection.delete_many({})
            current_app.logger.info(
                f"Documentos eliminados: {delete_result.deleted_count}"
            )

            # Insertar los documentos restaurados
            insert_result = catalog_collection.insert_many(processed_docs)
            inserted_count = len(insert_result.inserted_ids)

            # Registrar en auditoría
            audit_log(
                "database_restore_from_drive",
                user_id=session.get("user_id"),
                details={
                    "backup_id": backup_id,
                    "documents_restored": inserted_count,
                    "documents_deleted": delete_result.deleted_count,
                    "username": session.get("username", "desconocido"),
                },
            )

            current_app.logger.info(
                f"Restauración completada: {inserted_count} documentos insertados"
            )

            return jsonify(
                {
                    "success": True,
                    "message": f"Backup restaurado exitosamente. {inserted_count} documentos restaurados.",
                    "documents_restored": inserted_count,
                    "documents_deleted": delete_result.deleted_count,
                }
            )

        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    except requests.RequestException as e:
        current_app.logger.error(f"Error descargando desde Google Drive: {str(e)}")
        return (
            jsonify(
                {"success": False, "error": f"Error descargando el archivo: {str(e)}"}
            ),
            500,
        )
    except Exception as e:
        current_app.logger.error(f"Error en restore_drive_backup: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return (
            jsonify(
                {"success": False, "error": f"Error interno del servidor: {str(e)}"}
            ),
            500,
        )


@admin_bp.route("/reset_gdrive_token", methods=["POST"])
@admin_required
def reset_gdrive_token_route():
    import subprocess
    import sys

    try:
        script_path = os.path.join(
            os.path.dirname(__file__), "../../tools/db_utils/google_drive_utils.py"
        )
        result = subprocess.run(
            [sys.executable, script_path, "--reset-token"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            flash(
                "Token de Google Drive eliminado correctamente. Sigue las instrucciones para regenerar el refresh_token.",
                "success",
            )
            flash(result.stdout, "info")
        else:
            flash(f"Error al eliminar el token: {result.stderr}", "danger")
    except (OSError, PermissionError, subprocess.SubprocessError) as e:
        flash(f"Error al ejecutar el reseteo de token: {str(e)}", "danger")
    return redirect(url_for("maintenance.maintenance_dashboard"))


@admin_bp.route("/gdrive_upload_test", methods=["GET", "POST"])
@admin_required
def gdrive_upload_test():
    import os

    from werkzeug.utils import secure_filename

    from tools.db_utils.google_drive_utils import upload_to_drive

    uploaded_links = []
    if request.method == "POST":
        files = request.files.getlist("test_files")
        if not files or files[0].filename == "":
            flash("No se seleccionó ningún archivo.", "warning")
            return redirect(url_for("admin.gdrive_upload_test"))
        for file in files:
            if file.filename is None:
                continue
            filename = secure_filename(file.filename)
            temp_path = os.path.join("/tmp", filename)
            file.save(temp_path)
            try:
                result = upload_to_drive(temp_path)
                if result.get("success"):
                    # Extraer solo la URL del resultado
                    file_url = result.get("file_url", "#")
                    uploaded_links.append((filename, file_url))
                else:
                    # Si hay error, mostramos el mensaje de error
                    error_msg = result.get("error", "Error desconocido")
                    flash(f"Error al subir '{filename}': {error_msg}", "danger")
                flash(
                    f"Archivo '{filename}' subido correctamente a Google Drive.",
                    "success",
                )
            except (
                ConnectionError,
                TimeoutError,
                OSError,
                ValueError,
                AttributeError,
            ) as e:
                flash(f"Error al subir '{filename}': {str(e)}", "danger")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    return render_template(
        "admin/gdrive_upload_test.html", uploaded_links=uploaded_links
    )


@admin_bp.route("/backup/create-and-upload", methods=["POST"])
@admin_required
def create_and_upload_backup():
    """Crear backup y subirlo directamente a Google Drive"""
    try:
        backup_dir = get_backup_dir()

        # Crear backup JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json.gz")

        # Obtener datos de la base de datos
        db = get_mongo_db()

        # Crear estructura de backup
        backup_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "type": "json_backup",
            },
            "collections": {},
        }

        # Función para convertir objetos datetime a string
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            else:
                return obj

        # Obtener datos de las colecciones principales
        collections_to_backup = ["catalogs", "users"]

        for collection_name in collections_to_backup:
            try:
                collection = db[collection_name]
                documents = list(collection.find({}))

                # Convertir ObjectId y datetime para JSON serialization
                converted_documents = []
                for doc in documents:
                    # Crear una copia del documento
                    converted_doc = doc.copy()
                    if "_id" in converted_doc:
                        converted_doc["_id"] = str(converted_doc["_id"])
                    # Convertir todos los campos datetime
                    converted_doc = convert_datetime(converted_doc)
                    converted_documents.append(converted_doc)

                backup_data["collections"][collection_name] = converted_documents
                current_app.logger.info(
                    f"Colección {collection_name}: {len(documents)} documentos"
                )

            except Exception as e:
                current_app.logger.warning(
                    f"Error al respaldar colección {collection_name}: {str(e)}"
                )
                backup_data["collections"][collection_name] = []

        # Comprimir y escribir el backup
        import gzip
        import json

        json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
        compressed_data = gzip.compress(json_data.encode("utf-8"))

        with open(backup_file, "wb") as f:
            f.write(compressed_data)

        current_app.logger.info(f"Backup JSON creado: {backup_file}")

        # Subir a Google Drive
        try:
            from tools.db_utils.google_drive_utils import upload_to_drive

            # Subir archivo a Google Drive
            upload_result = upload_to_drive(backup_file, "Backups_CatalogoTablas")

            if not upload_result.get("success"):
                raise Exception(
                    upload_result.get("error", "Error desconocido al subir")
                )

            file_info = {
                "id": upload_result.get("file_id"),
                "name": upload_result.get("file_name"),
            }

            # Guardar información en la base de datos
            backups_collection = db["backups"]

            backup_record = {
                "filename": f"backup_{timestamp}.json.gz",
                "file_id": file_info.get("id"),
                "file_size": len(compressed_data),
                "uploaded_at": datetime.now(),
                "uploaded_by": session.get("username", "admin"),
                "description": "Backup directo a Google Drive",
                "type": "json_backup",
            }

            backups_collection.insert_one(backup_record)

            # Eliminar archivo local temporal
            try:
                os.remove(backup_file)
                current_app.logger.info(f"Archivo temporal eliminado: {backup_file}")
            except Exception as e:
                current_app.logger.warning(
                    f"No se pudo eliminar archivo temporal: {str(e)}"
                )

            return jsonify(
                {
                    "success": True,
                    "message": "Backup creado y subido exitosamente",
                    "file_id": file_info.get("id"),
                    "filename": f"backup_{timestamp}.json.gz",
                }
            )

        except Exception as drive_error:
            current_app.logger.error(
                f"Error al subir a Google Drive: {str(drive_error)}"
            )
            # Si falla la subida, mantener el archivo local
            return jsonify(
                {
                    "success": False,
                    "error": f"Backup creado localmente pero falló la subida a Google Drive: {str(drive_error)}",
                }
            )

    except Exception as e:
        current_app.logger.error(f"Error al crear backup directo: {str(e)}")
        return (
            jsonify({"success": False, "error": f"Error al crear backup: {str(e)}"}),
            500,
        )


@admin_bp.route("/backup/delete-local/<filename>", methods=["DELETE"])
@admin_required
def delete_local_backup_route(filename: str):
    """Eliminar un backup local"""
    try:
        backup_dir = get_backup_dir()
        backup_file = os.path.join(backup_dir, filename)

        # Verificar que el archivo existe
        if not os.path.exists(backup_file):
            return jsonify({"success": False, "error": "Archivo no encontrado"}), 404

        # Verificar que es un archivo de backup válido (usar la misma lógica que get_backup_files)
        valid_extensions = [
            ".bak",
            ".backup",
            ".zip",
            ".tar",
            ".gz",
            ".json.gz",
            ".sql",
            ".dump",
            ".old",
            ".back",
            ".tmp",
            ".swp",
            "~",
            ".csv",
            ".json",
        ]

        # Verificar que el archivo tiene una extensión válida
        if not any(filename.endswith(ext) for ext in valid_extensions):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Archivo no válido - extensión no permitida",
                    }
                ),
                400,
            )

        # Verificar que no contiene caracteres peligrosos
        if ".." in filename or "/" in filename or "\\" in filename:
            return (
                jsonify(
                    {"success": False, "error": "Archivo no válido - nombre inseguro"}
                ),
                400,
            )

        # Eliminar el archivo
        os.remove(backup_file)
        current_app.logger.info(f"Backup local eliminado: {filename}")

        # Registrar en auditoría
        audit_log("database_backup_deleted", details={"filename": filename})

        return jsonify(
            {"success": True, "message": f"Backup {filename} eliminado exitosamente"}
        )

    except Exception as e:
        current_app.logger.error(f"Error al eliminar backup local {filename}: {str(e)}")
        return (
            jsonify({"success": False, "error": f"Error al eliminar backup: {str(e)}"}),
            500,
        )


@admin_bp.route("/backup/upload-to-drive/<filename>", methods=["POST"])
@admin_required
def upload_backup_to_drive(filename: str):
    """
    Sube un archivo de respaldo a Google Drive y lo elimina localmente si tiene éxito.

    Args:
        filename (str): Nombre del archivo de respaldo a subir

    Returns:
        JSON: Respuesta con el resultado de la operación
    """
    import os
    import sys

    from flask import current_app, jsonify
    from werkzeug.utils import secure_filename

    # Agregar la ruta de tools/db_utils al path (compatible con aplicaciones empaquetadas)
    if getattr(sys, "frozen", False):
        # Aplicación empaquetada - buscar en el bundle
        app_dir = os.path.dirname(sys.executable)
        db_utils_paths = [
            os.path.join(app_dir, "..", "Frameworks", "tools", "db_utils"),
            os.path.join(app_dir, "tools", "db_utils"),
        ]
        # Usar la primera ruta que exista
        db_utils_path = None
        for path in db_utils_paths:
            if os.path.exists(path):
                db_utils_path = path
                break
    else:
        # Aplicación normal
        db_utils_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "tools", "db_utils"
        )

    if db_utils_path and db_utils_path not in sys.path:
        sys.path.insert(0, db_utils_path)

    try:
        from google_drive_utils import upload_to_drive
    except ImportError:
        # Si no se puede importar, Google Drive no estará disponible
        current_app.logger.warning(
            "Google Drive no disponible: no se puede importar google_drive_utils"
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Google Drive no disponible",
                    "message": "Las credenciales de Google Drive no están configuradas correctamente.",
                }
            ),
            503,
        )

    try:
        # Validar el nombre del archivo
        if ".." in filename or "/" in filename:
            current_app.logger.warning(
                f"Intento de acceso a ruta no permitida: {filename}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Nombre de archivo no válido",
                        "message": "El nombre del archivo contiene caracteres no permitidos.",
                    }
                ),
                400,
            )

        # Construir la ruta completa del archivo usando la función get_backup_dir()
        backup_dir = get_backup_dir()
        file_path = os.path.join(backup_dir, secure_filename(filename))

        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            current_app.logger.warning(f"Archivo no encontrado: {file_path}")
            return (
                jsonify(
                    {
                        "success": False,
                        "status": "error",
                        "error": "Archivo no encontrado",
                        "message": f"El archivo {filename} no existe en el servidor.",
                    }
                ),
                404,
            )

        # Obtener información del archivo local
        file_size = os.path.getsize(file_path)
        file_info = {
            "filename": filename,
            "file_size": file_size,
            "local_path": file_path,
            "last_modified": os.path.getmtime(file_path),
        }

        current_app.logger.info(f"Iniciando subida a Google Drive: {file_info}")

        # Subir a Google Drive
        result = upload_to_drive(file_path)

        if result.get("success"):
            # Obtener la URL de descarga directa
            file_id = result.get("file_id")
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            web_view_url = result.get(
                "file_url"
            )  # Usar la URL de vista web que ya viene de upload_to_drive

            # Guardar metadatos en la base de datos
            backup_metadata = {
                "filename": filename,
                "file_id": file_id,
                "file_size": file_size,
                "download_url": download_url,
                "web_view_url": web_view_url,
                "uploaded_at": datetime.utcnow(),
                "uploaded_by": (
                    current_user.id
                    if hasattr(current_user, "is_authenticated")
                    and current_user.is_authenticated
                    else None
                ),
                "status": "uploaded",
                "folder_name": result.get("folder_name", "Backups_CatalogoTablas"),
            }

            # Insertar en la colección de respaldos
            db = get_mongo_db()
            if db is not None:
                db.backups.insert_one(backup_metadata)

            # Eliminar el archivo local si la subida fue exitosa
            try:
                os.remove(file_path)
                current_app.logger.info(
                    f"Archivo {filename} eliminado localmente después de subir a Google Drive"
                )

                # Registrar la acción en el log de auditoría
                log_action(
                    action="backup_uploaded_to_drive",
                    message=f"Backup subido a Google Drive: {filename} ({file_size / 1024 / 1024:.2f} MB)",
                    details={
                        "file_id": file_id,
                        "file_name": filename,
                        "file_size": file_size,
                        "drive_folder": result.get(
                            "folder_name", "Backups_CatalogoTablas"
                        ),
                        "download_url": download_url,
                        "web_view_url": web_view_url,
                    },
                    user_id=(
                        current_user.id
                        if hasattr(current_user, "is_authenticated")
                        and current_user.is_authenticated
                        else None
                    ),
                    collection="backups",
                )

                # Preparar respuesta exitosa
                response_data = {
                    "success": True,
                    "message": "El respaldo se ha subido correctamente a Google Drive y se ha eliminado localmente.",
                    "file_info": {
                        "filename": filename,
                        "file_id": file_id,
                        "file_size": file_size,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "download_url": download_url,
                        "web_view_url": web_view_url,
                        "uploaded_at": backup_metadata["uploaded_at"].isoformat(),
                        "folder_name": result.get(
                            "folder_name", "Backups_CatalogoTablas"
                        ),
                    },
                }

                current_app.logger.info(
                    f"Subida a Google Drive completada: {response_data}"
                )
                return jsonify(response_data)

            except (OSError, PermissionError) as e:
                error_msg = f"Error al eliminar el archivo local {filename}: {str(e)}"
                current_app.logger.error(error_msg, exc_info=True)

                # Registrar el error en el log de auditoría
                log_action(
                    action="backup_upload_error",
                    message=f"Error al eliminar archivo local después de subir a Google Drive: {filename}",
                    details={
                        "error": str(e),
                        "file_name": filename,
                        "file_size": file_size,
                        "drive_folder": result.get(
                            "folder_name", "Backups_CatalogoTablas"
                        ),
                    },
                    user_id=(
                        current_user.id
                        if hasattr(current_user, "is_authenticated")
                        and current_user.is_authenticated
                        else None
                    ),
                    collection="backups",
                )

                # Si falla la eliminación local, la subida a Drive fue exitosa, así que lo consideramos un éxito parcial
                return (
                    jsonify(
                        {
                            "success": True,
                            "warning": "El archivo se subió a Google Drive pero no se pudo eliminar localmente.",
                            "error": error_msg,
                            "file_info": {
                                "filename": result.get("filename"),
                                "file_id": result.get("file_id"),
                                "download_url": result.get("download_url"),
                                "web_view_url": result.get("web_view_url"),
                                "folder_name": result.get("folder_name"),
                            },
                        }
                    ),
                    207,
                )  # Código 207 Multi-Status para éxito parcial

        else:
            error_msg = f"Error al subir a Google Drive: {result.get('error')}"
            current_app.logger.error(error_msg)

            # Registrar el error en el log de auditoría
            log_action(
                action="backup_upload_failed",
                message=f"Error al subir archivo a Google Drive: {filename}",
                details={
                    "error": result.get("error", "Error desconocido"),
                    "file_name": filename,
                    "file_size": file_size,
                },
                user_id=(
                    current_user.id
                    if hasattr(current_user, "is_authenticated")
                    and current_user.is_authenticated
                    else None
                ),
                collection="backups",
            )

            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Error desconocido"),
                        "message": "El archivo no se pudo subir a Google Drive. Por favor, inténtalo de nuevo.",
                    }
                ),
                500,
            )

    except (
        ConnectionError,
        TimeoutError,
        OSError,
        ValueError,
        AttributeError,
        KeyError,
        TypeError,
    ) as e:
        error_msg = f"Error inesperado en upload_backup_to_drive: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)

        # Registrar el error inesperado en el log de auditoría
        log_action(
            action="backup_upload_error",
            message=f"Error inesperado al subir archivo a Google Drive: {filename}",
            details={
                "error": str(e),
                "file_name": filename,
                "traceback": traceback.format_exc(),
            },
            user_id=(
                current_user.id
                if hasattr(current_user, "is_authenticated")
                and current_user.is_authenticated
                else None
            ),
            collection="backups",
        )

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Error interno del servidor",
                    "message": "Ocurrió un error inesperado al procesar la solicitud.",
                    "details": str(e) if current_app.config.get("DEBUG") else None,
                }
            ),
            500,
        )


@admin_bp.route("/drive-backups")
@admin_required
def list_drive_backups():
    """
    Muestra una lista de todos los respaldos almacenados en Google Drive.
    Devuelve JSON si se solicita via AJAX, HTML si es una petición normal.
    """
    try:
        # Verificar si existen las credenciales antes de intentar listar
        credentials_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "tools",
            "db_utils",
            "credentials.json",
        )
        if not os.path.exists(credentials_path):
            # Si es una petición AJAX, devolver JSON informativo
            if request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest" or "application/json" in request.headers.get(
                "Accept", ""
            ):
                return jsonify(
                    {
                        "status": "success",
                        "backups": [
                            {
                                "_id": "no-credentials",
                                "filename": "Google Drive no configurado",
                                "file_size": 0,
                                "uploaded_at": "",
                                "uploaded_by_name": "Sistema",
                                "download_url": "",
                                "web_view_url": "",
                                "is_placeholder": True,
                            }
                        ],
                        "message": "Las credenciales de Google Drive no están configuradas",
                    }
                )

        # Listar archivos reales en Google Drive
        files = list_files_in_folder("Backups_CatalogoTablas")

        # ... existing code ...
        processed_backups = []
        for file_info in files:
            # Convertir la fecha de string a datetime si es necesario
            uploaded_at = file_info.get("modified", "")
            if uploaded_at and isinstance(uploaded_at, str):
                try:
                    from datetime import datetime

                    # Intentar parsear la fecha en diferentes formatos
                    for fmt in [
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S",
                    ]:
                        try:
                            uploaded_at = datetime.strptime(uploaded_at, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # Si no se puede parsear, mantener como string
                        uploaded_at = uploaded_at
                except Exception:
                    uploaded_at = uploaded_at

            backup = {
                "_id": file_info["id"],
                "filename": file_info["name"],
                "file_size": file_info["size"],
                "uploaded_at": uploaded_at,
                "uploaded_by_name": "Google Drive",
                "download_url": file_info.get("download_url", ""),
                "web_view_url": file_info.get("download_url", ""),
                "is_placeholder": False,
            }
            processed_backups.append(backup)

        # Si es una petición AJAX, devolver JSON
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest" or "application/json" in request.headers.get(
            "Accept", ""
        ):
            return jsonify({"status": "success", "backups": processed_backups})

        # ... existing code for HTML response ...
        # Si es una petición normal, devolver HTML
        return render_template(
            "admin/drive_backups.html",
            backups=processed_backups,
            title="Respaldo en Google Drive",
            active_page="drive_backups",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error al listar respaldos de Google Drive: {str(e)}", exc_info=True
        )

        # Si es una petición AJAX, devolver JSON de error más informativo
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest" or "application/json" in request.headers.get(
            "Accept", ""
        ):
            return jsonify(
                {
                    "status": "success",
                    "backups": [
                        {
                            "_id": "error",
                            "filename": "Error de configuración",
                            "file_size": 0,
                            "uploaded_at": "",
                            "uploaded_by_name": "Sistema",
                            "download_url": "",
                            "web_view_url": "",
                            "is_placeholder": True,
                            "error_message": str(e),
                        }
                    ],
                    "message": "Error al acceder a Google Drive. Verifica la configuración.",
                }
            )

        flash("Error al cargar la lista de respaldos de Google Drive", "error")
        # En lugar de redirigir, mostrar la página de Google Drive con un mensaje de error
        return render_template(
            "admin/drive_backups.html",
            backups=[
                {
                    "_id": "error",
                    "filename": "Error de configuración",
                    "file_size": 0,
                    "uploaded_at": "",
                    "uploaded_by_name": "Sistema",
                    "download_url": "",
                    "web_view_url": "",
                    "is_placeholder": True,
                    "error_message": str(e),
                }
            ],
            title="Respaldo en Google Drive",
            active_page="drive_backups",
        )


@admin_bp.route("/truncate_log", methods=["POST"])
@admin_required
def truncate_log_route():
    import subprocess
    import sys

    log_file = request.form.get("log_file")
    lines = request.form.get("lines")
    date = request.form.get("date")
    script_path = os.path.join(os.path.dirname(__file__), "../../tools/log_utils.py")
    cmd = [sys.executable, script_path, "--file", log_file]
    if lines:
        cmd += ["--lines", lines]
    elif date:
        cmd += ["--date", date]
    else:
        # Si la petición es AJAX o JSON, responde con JSON
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Debes indicar número de líneas o fecha.",
                    }
                ),
                400,
            )
        flash("Debes indicar número de líneas o fecha.", "warning")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            flash(result.stdout, "success")
        else:
            flash(result.stderr, "danger")
    except (OSError, PermissionError, subprocess.SubprocessError) as e:
        flash(f"Error al truncar el log: {str(e)}", "danger")
    return redirect(url_for("maintenance.maintenance_dashboard"))


# Función para registrar los blueprints
def register_admin_blueprints(app: Any) -> None:
    """
    Función para registrar blueprints adicionales de administración.
    Nota: admin_logs_bp ya está registrado en __init__.py
    """
    try:
        # No es necesario registrar admin_logs_bp aquí ya que ya está registrado en __init__.py
        # con el prefijo correcto
        pass
    except (AttributeError, ValueError, TypeError) as e:
        app.logger.error(f"Error en register_admin_blueprints: {str(e)}")


@admin_bp.route("/api/system-status")
@admin_required
def api_system_status():
    """API endpoint para obtener el estado del sistema en tiempo real"""
    try:
        from app.monitoring import check_system_health

        # Forzar actualización inmediata del estado del sistema
        check_system_health()

        # Obtener datos actualizados
        data = get_system_status_data()

        # Reestructurar datos para que coincidan con lo que espera el JavaScript
        system_metrics = (
            data.get("health", {}).get("metrics", {}).get("system_status", {})
        )

        # Validar que tenemos datos válidos
        if not system_metrics or system_metrics.get("cpu_usage", 0) == 0:
            # Si no hay datos, intentar obtenerlos directamente
            import psutil

            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_usage = psutil.cpu_percent(interval=0.1)

            system_metrics = {
                "cpu_usage": cpu_usage,
                "memory_usage": {
                    "percent": memory.percent,
                    "used_mb": round(memory.used / (1024 * 1024), 2),
                    "total_mb": round(memory.total / (1024 * 1024), 2),
                },
                "disk_usage": {
                    "percent": disk.percent,
                    "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                },
            }

        response_data = {"system_status": system_metrics}

        current_app.logger.info(f"API system-status devolviendo: {response_data}")
        return jsonify({"status": "success", "data": response_data})

    except (
        ConnectionError,
        TimeoutError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"Error en api_system_status: {str(e)}", exc_info=True)
        return (
            jsonify(
                {"status": "error", "message": "Error al obtener estado del sistema"}
            ),
            500,
        )


@admin_bp.route("/api/drive-backups")
@admin_required
def api_drive_backups():
    """API para obtener la lista de respaldos en Google Drive"""
    try:
        db = get_mongo_db()
        if db is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo conectar a la base de datos",
                    }
                ),
                500,
            )

        # Obtener respaldos de la base de datos
        backups = list(db.backups.find({}, {"_id": 0}).sort("uploaded_at", -1))

        # Convertir ObjectId a string si existe
        for backup in backups:
            if "uploaded_at" in backup:
                backup["uploaded_at"] = backup["uploaded_at"].isoformat()

        return jsonify({"success": True, "backups": backups, "count": len(backups)})

    except Exception as e:
        current_app.logger.error(f"Error al obtener respaldos de Drive: {str(e)}")
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"}), 500


@admin_bp.route("/api/cache-stats")
@admin_required
def api_cache_stats():
    """API endpoint para obtener las estadísticas del caché en tiempo real"""
    try:
        cache_stats = get_cache_stats()
        return jsonify({"status": "success", "data": cache_stats})

    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en api_cache_stats: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Error al obtener estadísticas del caché",
                }
            ),
            500,
        )


@admin_bp.route("/api/test-cache")
@admin_required
def test_cache():
    """Endpoint temporal para generar actividad en el caché y probar las estadísticas"""
    import random

    from app.cache_system import get_cache, set_cache

    try:
        # Generar algunas operaciones de caché para pruebas
        test_keys = [f"test_key_{i}" for i in range(5)]

        for key in test_keys:
            # Intentar obtener valor (generará miss si no existe)
            value = get_cache(key)

            if value is None:
                # Si no existe, crear uno nuevo
                set_cache(key, f"test_value_{random.randint(1, 100)}", ttl=300)

        # Hacer algunas consultas adicionales para generar hits
        for _i in range(3):
            get_cache(f"test_key_{random.randint(0, 4)}")

        cache_stats = get_cache_stats()
        return jsonify(
            {
                "status": "success",
                "message": "Actividad de caché generada correctamente",
                "data": cache_stats,
            }
        )

    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error en test_cache: {str(e)}", exc_info=True)
        return (
            jsonify(
                {"status": "error", "message": "Error al generar actividad del caché"}
            ),
            500,
        )


@admin_bp.route("/api/test-database")
@admin_required
def test_database():
    """Endpoint para probar la conexión de base de datos manualmente"""
    try:
        from app import monitoring
        from app.database import get_mongo_client

        # Intentar obtener cliente y verificar conexión
        client = get_mongo_client()
        success = monitoring.check_database_health(client)

        database_status = monitoring._app_metrics.get(
            "database_status",
            {
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_available": False,
                "response_time_ms": 0,
                "error": "No se pudo verificar el estado",
            },
        )

        return jsonify(
            {
                "status": "success",
                "message": "Verificación de base de datos completada",
                "data": database_status,
            }
        )

    except (
        ConnectionError,
        TimeoutError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"Error en test_database: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Error al verificar la base de datos",
                    "data": {
                        "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "is_available": False,
                        "response_time_ms": 0,
                        "error": str(e),
                    },
                }
            ),
            500,
        )


# Ruta movida a scripts_bp para evitar conflictos
# @admin_bp.route("/tools")
# @admin_required
# def tools_dashboard():
#     """
#     Dashboard de herramientas y scripts del sistema.
#     Requiere login de administrador.
#     """
#     return render_template('admin/tools_dashboard.html')


@admin_bp.route("/tools-test")
@admin_required
def tools_dashboard_test():
    """
    Dashboard de prueba para verificar que las pestañas funcionan.
    """
    return render_template("admin/tools_dashboard_simple.html")


@admin_bp.route("/password-management")
@admin_required
def password_management():
    """
    Panel de gestión de contraseñas temporales para administradores.
    """
    try:
        users_collection = get_users_collection()
        if users_collection is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.dashboard_admin"))

        # Obtener usuarios con contraseñas temporales
        temp_password_users = list(
            users_collection.find(
                {
                    "$or": [
                        {"temp_password": True},
                        {"must_change_password": True},
                        {"password_reset_required": True},
                    ]
                }
            )
        )

        # Obtener todos los usuarios para estadísticas
        all_users = list(users_collection.find({}))

        # Preparar datos para el template
        temp_users_data = []
        for user in temp_password_users:
            # Generar contraseña temporal actual (patrón conocido)
            temp_pass = f"{user.get('username', 'user')}123"

            temp_users_data.append(
                {
                    "id": str(user.get("_id")),
                    "username": user.get("username", "N/A"),
                    "email": user.get("email", "N/A"),
                    "nombre": user.get("nombre", user.get("name", "N/A")),
                    "role": user.get("role", "user"),
                    "temp_password": temp_pass,
                    "temp_password_flag": user.get("temp_password", False),
                    "must_change_password": user.get("must_change_password", False),
                    "password_reset_required": user.get(
                        "password_reset_required", False
                    ),
                    "temp_password_pattern": user.get(
                        "temp_password_pattern", temp_pass
                    ),
                    "temp_password_updated_at": user.get("temp_password_updated_at"),
                    "flags_cleared_at": user.get("flags_cleared_at"),
                    "last_login": user.get("last_login"),
                }
            )

        # Estadísticas
        stats = {
            "total_users": len(all_users),
            "temp_password_users": len(temp_password_users),
            "percentage": (
                round((len(temp_password_users) / len(all_users) * 100), 1)
                if all_users
                else 0
            ),
            "admin_users": len([u for u in all_users if u.get("role") == "admin"]),
            "regular_users": len(
                [u for u in all_users if u.get("role", "user") == "user"]
            ),
        }

        # Obtener usuarios normales (sin contraseñas temporales)
        normal_users = list(
            users_collection.find(
                {
                    "$and": [
                        {"temp_password": {"$ne": True}},
                        {"must_change_password": {"$ne": True}},
                        {"password_reset_required": {"$ne": True}},
                    ]
                }
            )
        )

        normal_users_data = []
        for user in normal_users:
            normal_users_data.append(
                {
                    "id": str(user.get("_id")),
                    "username": user.get("username", "N/A"),
                    "email": user.get("email", "N/A"),
                    "name": user.get("nombre", user.get("name", "N/A")),
                    "role": user.get("role", "user"),
                    "verified": user.get("verified", False),
                    "last_login": user.get("last_login"),
                }
            )

        return render_template(
            "admin/password_management.html",
            temp_users=temp_users_data,
            normal_users=normal_users_data,
            stats=stats,
        )

    except Exception as e:
        logger.error(f"Error en password_management: {str(e)}", exc_info=True)
        flash(f"Error al cargar gestión de contraseñas: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_bp.route("/password-management/reset/<user_id>", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    """
    Generar nueva contraseña temporal para un usuario específico.
    """
    try:
        from bson import ObjectId

        users_collection = get_users_collection()
        if users_collection is None:
            return jsonify(
                {"success": False, "error": "Error de conexión a base de datos"}
            )

        # Buscar el usuario
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"})

        username = user.get("username", "user")
        new_temp_password = f"{username}123"

        # Actualizar contraseña y flags
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password": generate_password_hash(
                        new_temp_password, method="pbkdf2:sha256"
                    ),
                    "temp_password": True,
                    "must_change_password": True,
                    "password_reset_required": True,
                    "temp_password_updated_at": datetime.utcnow().isoformat(),
                    "temp_password_pattern": new_temp_password,
                    "password_type": "werkzeug",
                    "admin_reset_by": session.get("username", "admin"),
                    "admin_reset_at": datetime.utcnow().isoformat(),
                }
            },
        )

        if result.modified_count > 0:
            logger.info(
                f"Contraseña temporal restablecida para {username} por admin {session.get('username')}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Contraseña temporal restablecida para {username}",
                    "new_password": new_temp_password,
                }
            )
        else:
            return jsonify(
                {"success": False, "error": "No se pudo actualizar la contraseña"}
            )

    except Exception as e:
        logger.error(f"Error reseteando contraseña: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


@admin_bp.route("/password-management/clear-flags/<user_id>", methods=["POST"])
@admin_required
def clear_user_flags(user_id):
    """
    Limpiar flags de contraseña temporal de un usuario.
    """
    try:
        from bson import ObjectId

        users_collection = get_users_collection()
        if users_collection is None:
            return jsonify(
                {"success": False, "error": "Error de conexión a base de datos"}
            )

        # Buscar el usuario
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"})

        username = user.get("username", "user")

        # Limpiar flags
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "temp_password": False,
                    "must_change_password": False,
                    "password_reset_required": False,
                    "flags_cleared_at": datetime.utcnow().isoformat(),
                    "flags_cleared_by": session.get("username", "admin"),
                    "flags_cleared_manually": True,
                }
            },
        )

        if result.modified_count > 0:
            logger.info(
                f"Flags limpiados para {username} por admin {session.get('username')}"
            )
            return jsonify(
                {"success": True, "message": f"Flags limpiados para {username}"}
            )
        else:
            return jsonify(
                {"success": False, "error": "No se pudieron limpiar los flags"}
            )

    except Exception as e:
        logger.error(f"Error limpiando flags: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


@admin_bp.route("/password-management/bulk-action", methods=["POST"])
@admin_required
def bulk_password_action():
    """
    Acciones masivas sobre usuarios con contraseñas temporales.
    """
    try:
        action = request.json.get("action") if request.json else None
        user_ids = request.json.get("user_ids", []) if request.json else []

        if not action or not user_ids:
            return jsonify(
                {"success": False, "error": "Acción o usuarios no especificados"}
            )

        users_collection = get_users_collection()
        if users_collection is None:
            return jsonify(
                {"success": False, "error": "Error de conexión a base de datos"}
            )

        results = []

        if action == "clear_all_flags":
            for user_id in user_ids:
                try:
                    from bson import ObjectId

                    result = users_collection.update_one(
                        {"_id": ObjectId(user_id)},
                        {
                            "$set": {
                                "temp_password": False,
                                "must_change_password": False,
                                "password_reset_required": False,
                                "flags_cleared_at": datetime.utcnow().isoformat(),
                                "flags_cleared_by": session.get("username", "admin"),
                                "bulk_action": True,
                            }
                        },
                    )
                    results.append(
                        {"user_id": user_id, "success": result.modified_count > 0}
                    )
                except Exception as e:
                    results.append(
                        {"user_id": user_id, "success": False, "error": str(e)}
                    )

        elif action == "reset_all_passwords":
            for user_id in user_ids:
                try:
                    from bson import ObjectId

                    user = users_collection.find_one({"_id": ObjectId(user_id)})
                    if user:
                        username = user.get("username", "user")
                        new_temp_password = f"{username}123"

                        result = users_collection.update_one(
                            {"_id": ObjectId(user_id)},
                            {
                                "$set": {
                                    "password": generate_password_hash(
                                        new_temp_password, method="pbkdf2:sha256"
                                    ),
                                    "temp_password": True,
                                    "must_change_password": True,
                                    "password_reset_required": True,
                                    "temp_password_updated_at": datetime.utcnow().isoformat(),
                                    "temp_password_pattern": new_temp_password,
                                    "admin_reset_by": session.get("username", "admin"),
                                    "bulk_action": True,
                                }
                            },
                        )
                        results.append(
                            {"user_id": user_id, "success": result.modified_count > 0}
                        )
                except Exception as e:
                    results.append(
                        {"user_id": user_id, "success": False, "error": str(e)}
                    )

        successful = len([r for r in results if r.get("success")])
        total = len(results)

        logger.info(
            f"Acción masiva '{action}' por admin {session.get('username')}: {successful}/{total} exitosos"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Acción completada: {successful}/{total} usuarios procesados",
                "results": results,
            }
        )

    except Exception as e:
        logger.error(f"Error en acción masiva: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


@admin_bp.route("/assign-temp-password/<user_id>", methods=["POST"])
@admin_required
def assign_temp_password(user_id):
    """
    Asignar contraseña temporal a un usuario normal.
    """
    try:
        from bson import ObjectId
        from werkzeug.security import generate_password_hash

        from app.models.database import get_users_collection

        users_collection = get_users_collection()
        if users_collection is None:
            return jsonify(
                {"success": False, "error": "No se pudo acceder a la base de datos"}
            )

        # Buscar el usuario
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"})

        username = user.get("username")
        if not username:
            return jsonify(
                {"success": False, "error": "Usuario sin nombre de usuario válido"}
            )

        # Generar contraseña temporal con patrón conocido
        temp_password = f"{username}123"
        hashed_password = generate_password_hash(temp_password, method="pbkdf2:sha256")

        # Actualizar usuario con flags temporales
        from datetime import datetime

        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password": hashed_password,
                    "temp_password": True,
                    "must_change_password": True,
                    "password_reset_required": True,
                    "temp_password_pattern": temp_password,
                    "temp_password_updated_at": datetime.now().isoformat(),
                    "temp_password_assigned_by": session.get("username", "admin"),
                    "temp_password_reason": "Acceso sin correo - Asignación manual por administrador",
                }
            },
        )

        if result.modified_count > 0:
            logger.info(
                f"Contraseña temporal asignada a {username} por admin {session.get('username')}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Contraseña temporal asignada correctamente a {username}",
                    "temp_password": temp_password,
                }
            )
        else:
            return jsonify(
                {"success": False, "error": "No se pudo actualizar el usuario"}
            )

    except Exception as e:
        logger.error(f"Error asignando contraseña temporal: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


app = None
try:
    from flask import current_app as flask_current_app

    # Simplemente usar current_app directamente sin _get_current_object
    app = flask_current_app
except (RuntimeError, ImportError):
    try:
        import __main__

        app = getattr(__main__, "app", None)
    except Exception:
        app = None

# Temporalmente deshabilitado para evitar conflictos
# if app is not None:
#     register_admin_blueprints(app)
