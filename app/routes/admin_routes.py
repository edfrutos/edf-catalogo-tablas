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
from app.routes.admin.admin_verify_users import register_admin_verify_user_routes
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
            normalize_catalog_rows(catalog)
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

        # Procesar imágenes para cada fila (igual que en ver_tabla)
        if catalog.get("data"):
            from app.utils.image_utils import get_images_for_template

            for i, row in enumerate(catalog["data"]):
                # Usar función unificada para obtener URLs de imágenes
                image_data = get_images_for_template(row)
                # Añade imagen_urls, num_imagenes, tiene_imagenes
                row.update(image_data)

                current_app.logger.info(
                    f"[DEBUG][ADMIN] URLs de imágenes para fila {i}: {row.get('imagen_urls', [])}"
                )
                current_app.logger.info(
                    f"[DEBUG][ADMIN] Total de imágenes en fila {i}: {len(row.get('imagen_urls', []))}"
                )

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


@admin_bp.route("/usuarios/bulk_upload", methods=["GET", "POST"])
@admin_required
def bulk_upload_usuarios():
    """Gestión de usuarios en masa mediante archivo CSV"""
    try:
        if request.method == "POST":
            if "csv_file" not in request.files:
                flash("No se seleccionó ningún archivo", "error")
                return redirect(request.url)

            file = request.files["csv_file"]
            if file.filename == "":
                flash("No se seleccionó ningún archivo", "error")
                return redirect(request.url)

            if not file.filename.endswith(  # pyright: ignore[reportOptionalMemberAccess]
                ".csv"
            ):  # pyright: ignore[reportOptionalMemberAccess]
                flash("El archivo debe ser un CSV", "error")
                return redirect(request.url)

            # Procesar el archivo CSV
            import csv
            import io
            import random
            import string
            from datetime import datetime

            users_col = get_users_collection()
            if users_col is None:
                flash("Error: No se pudo acceder a la colección de usuarios", "error")
                return redirect(request.url)

            # Leer el archivo CSV con manejo de diferentes codificaciones
            file_content = file.read()
            csv_content = None

            # Intentar diferentes codificaciones
            encodings = [
                "utf-8",
                "utf-8-sig",
                "latin-1",
                "iso-8859-1",
                "cp1252",
                "windows-1252",
            ]

            for encoding in encodings:
                try:
                    csv_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if csv_content is None:
                flash(
                    "Error: No se pudo leer el archivo CSV. Verifique que el archivo esté en una codificación válida (UTF-8, ISO-8859-1, etc.)",
                    "error",
                )
                return redirect(request.url)

            csv_reader = csv.DictReader(io.StringIO(csv_content))

            # Validar que las columnas requeridas estén presentes
            required_columns = ["username", "email"]
            if not all(
                col in (csv_reader.fieldnames or []) for col in required_columns
            ):
                flash(
                    "El archivo CSV debe contener las columnas: username, email",
                    "error",
                )
                return redirect(request.url)

            # Procesar usuarios
            usuarios_procesados = []
            usuarios_exitosos = 0
            usuarios_duplicados = 0
            usuarios_error = 0

            for row_num, row in enumerate(
                csv_reader, start=2
            ):  # Empezar en 2 porque la fila 1 es el encabezado
                try:
                    username = row["username"].strip()
                    email = row["email"].strip()

                    # Validaciones básicas
                    if not username or not email:
                        usuarios_error += 1
                        usuarios_procesados.append(
                            {
                                "row": row_num,
                                "username": username,
                                "email": email,
                                "status": "error",
                                "message": "Username y email son obligatorios",
                            }
                        )
                        continue

                    # Verificar si el usuario ya existe
                    existing_user = users_col.find_one(
                        {"$or": [{"email": email}, {"username": username}]}
                    )

                    if existing_user:
                        usuarios_duplicados += 1
                        usuarios_procesados.append(
                            {
                                "row": row_num,
                                "username": username,
                                "email": email,
                                "status": "duplicate",
                                "message": "Usuario ya existe",
                            }
                        )
                        continue

                    # Generar contraseña temporal
                    temp_password = "".join(
                        random.choices(string.ascii_letters + string.digits, k=12)
                    )

                    # Crear el usuario
                    new_user = {
                        "username": username,
                        "email": email,
                        "password": generate_password_hash(
                            temp_password, method="pbkdf2:sha256"
                        ),
                        "role": "user",
                        "verified": True,
                        "created_at": datetime.utcnow(),
                        "temp_password": True,
                        "must_change_password": True,
                        "password_created_at": datetime.utcnow().isoformat(),
                    }

                    result = users_col.insert_one(new_user)

                    if result.inserted_id:
                        usuarios_exitosos += 1
                        usuarios_procesados.append(
                            {
                                "row": row_num,
                                "username": username,
                                "email": email,
                                "status": "success",
                                "message": f"Usuario creado con contraseña temporal: {temp_password}",
                                "temp_password": temp_password,
                            }
                        )
                    else:
                        usuarios_error += 1
                        usuarios_procesados.append(
                            {
                                "row": row_num,
                                "username": username,
                                "email": email,
                                "status": "error",
                                "message": "Error al crear usuario en la base de datos",
                            }
                        )

                except Exception as e:
                    usuarios_error += 1
                    usuarios_procesados.append(
                        {
                            "row": row_num,
                            "username": row.get("username", "N/A"),
                            "email": row.get("email", "N/A"),
                            "status": "error",
                            "message": f"Error de procesamiento: {str(e)}",
                        }
                    )

            # Mostrar resultados
            flash(
                f"Procesamiento completado: {usuarios_exitosos} creados, {usuarios_duplicados} duplicados, {usuarios_error} errores",
                "info",
            )

            return render_template(
                "admin/bulk_upload_result.html",
                usuarios_procesados=usuarios_procesados,
                total_creados=usuarios_exitosos,
                total_duplicados=usuarios_duplicados,
                total_errores=usuarios_error,
            )

        return render_template("admin/bulk_upload.html")

    except Exception as e:
        logger.error(f"Error en bulk_upload_usuarios: {str(e)}", exc_info=True)
        flash(f"Error al procesar la carga masiva: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))


@admin_bp.route("/usuarios/download_template")
@admin_required
def download_csv_template():
    """Descargar plantilla CSV para carga masiva de usuarios"""
    try:
        import csv
        import io

        # Crear el contenido del CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow(["username", "email"])

        # Escribir algunos ejemplos
        writer.writerow(["usuario1", "usuario1@ejemplo.com"])
        writer.writerow(["usuario2", "usuario2@ejemplo.com"])
        writer.writerow(["usuario3", "usuario3@ejemplo.com"])

        # Preparar la respuesta
        output.seek(0)

        from flask import Response

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=usuarios_template.csv"
            },
        )

    except Exception as e:
        logger.error(f"Error al generar plantilla CSV: {str(e)}", exc_info=True)
        flash(f"Error al generar la plantilla: {str(e)}", "error")
        return redirect(url_for("admin.bulk_upload_usuarios"))


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
            # Validar el nombre del archivo para evitar ataques de traversal de
            # directorio
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

                            # Si el archivo es más grande que el tamaño estimado,
                            # truncarlo
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
                            # Intentar extraer la fecha de la línea de log (formato
                            # típico: [YYYY-MM-DD HH:MM:SS,mmm])
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
                                    # Si hay un error al parsear la fecha, mantener la
                                    # línea
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
            normalize_catalog_rows(catalog)
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

        try:
            catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        except Exception as e:
            logger.error(
                f"[ADMIN] Error al convertir catalog_id a ObjectId: {catalog_id}, error: {e}"
            )
            flash("ID de catálogo inválido", "error")
            return redirect(url_for("admin.dashboard_admin"))

        if not catalog:
            logger.warning(
                f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
            )
            flash("Catálogo no encontrado", "warning")
            return render_template(
                "admin/ver_catalogo.html", catalog=None, error="Catálogo no encontrado"
            )

        # --- Start of Refactoring ---

        def get_final_url(file_identifier):
            if not isinstance(file_identifier, str) or not file_identifier.strip():
                return None, None

            filename = file_identifier.split("/")[-1]

            if file_identifier.startswith("http"):
                if "s3.amazonaws.com" in file_identifier:
                    return f"/admin/s3/{filename}", filename
                return file_identifier, filename

            if file_identifier.startswith("/"):
                return file_identifier, filename

            s3_url = get_s3_url(file_identifier)
            if s3_url:
                return f"/admin/s3/{filename}", filename

            return f"/static/uploads/{file_identifier}", filename

        if "data" in catalog and catalog["data"]:
            for i, row in enumerate(catalog["data"]):
                if not isinstance(row, dict):
                    logger.warning(
                        f"[ADMIN] Fila {i} ignorada por no ser un dict: {row}"
                    )
                    continue

                # 1. Consolidate and process documents
                processed_documents = []
                seen_documents = set()
                doc_fields = [k for k in row if k.lower().startswith("document")]

                for field in doc_fields:
                    doc_values = row.get(field)
                    if not doc_values:
                        continue

                    doc_list = (
                        [doc_values] if isinstance(doc_values, str) else doc_values
                    )

                    if isinstance(doc_list, list):
                        for doc_item in doc_list:
                            if (
                                doc_item
                                and isinstance(doc_item, str)
                                and doc_item.strip() not in seen_documents
                            ):
                                doc_item_clean = doc_item.strip()
                                seen_documents.add(doc_item_clean)
                                url, filename = get_final_url(doc_item_clean)
                                if url and filename:
                                    ext = (
                                        filename.split(".")[-1].lower()
                                        if "." in filename
                                        else "link"
                                    )
                                    processed_documents.append(
                                        {
                                            "url": url,
                                            "name": ext.upper(),
                                            "filename": filename,
                                        }
                                    )

                row["processed_documents"] = processed_documents

                # 2. Consolidate and process images
                processed_images = []
                seen_images = set()
                image_fields = [
                    k for k in row if k.lower() in ["images", "imagenes", "imagen"]
                ]

                for field in image_fields:
                    img_values = row.get(field)
                    if not img_values:
                        continue

                    img_list = (
                        [img_values] if isinstance(img_values, str) else img_values
                    )

                    if isinstance(img_list, list):
                        for img_item in img_list:
                            if (
                                img_item
                                and isinstance(img_item, str)
                                and img_item.strip() not in seen_images
                            ):
                                img_item_clean = img_item.strip()
                                seen_images.add(img_item_clean)
                                url, _ = get_final_url(img_item_clean)
                                if url:
                                    processed_images.append(url)

                row["imagen_urls"] = processed_images

                # 3. Process Multimedia
                if "Multimedia" in row and row["Multimedia"]:
                    media_item = row["Multimedia"]
                    url, filename = get_final_url(media_item)
                    row["multimedia_url"] = url
                    row["multimedia_filename"] = filename if filename else ""

        # --- End of Refactoring ---

        catalog["collection_source"] = collection_source
        catalog["_id_str"] = str(catalog["_id"])

        if "created_at" in catalog and catalog["created_at"]:
            if isinstance(catalog["created_at"], str):
                catalog["created_at_formatted"] = catalog["created_at"]
            else:
                catalog["created_at_formatted"] = catalog["created_at"].strftime(
                    "%d/%m/%Y %H:%M"
                )
        else:
            catalog["created_at_formatted"] = "Fecha desconocida"

        normalize_catalog_rows(catalog)

        logger.info(
            f"[ADMIN] Mostrando catálogo desde {collection_source}: {catalog.get('name', 'Sin nombre')}"
        )
        return_url = request.args.get("return_url") or request.referrer

        if return_url and "editar-fila" in return_url:
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

        row_data = get_catalog_rows(catalog)[row_index]
        logger.info(f"[ADMIN_EDIT_ROW] 🔍 row_data obtenido: {row_data}")
        logger.info(f"[ADMIN_EDIT_ROW] 📋 row_data tipo: {type(row_data)}")
        logger.info(
            f"[ADMIN_EDIT_ROW] 📋 row_data keys: {list(row_data.keys()) if isinstance(row_data, dict) else 'No es dict'}"
        )

        # Procesar campos de Documentación - crear campos individuales para el
        # template (igual que en ver_catalogo_unificado)
        if "Documentación" in row_data and isinstance(row_data["Documentación"], list):
            for i, doc in enumerate(row_data["Documentación"]):
                if doc and doc.strip():  # Solo si el documento no está vacío
                    row_data[f"Documentación_{i}"] = doc.strip()
                    logger.debug(
                        f"[ADMIN_EDIT_ROW] Creado campo Documentación_{i} = {doc.strip()}"
                    )

        # Procesar imágenes - unificar campos 'images' e 'imagenes' (igual que en
        # ver_catalogo_unificado)
        from app.utils.s3_utils import get_s3_url

        # Procesar imágenes - unificar campos 'images' e 'imagenes'
        imagenes_a_procesar = []

        # Recopilar imágenes de ambos campos
        if "images" in row_data and row_data["images"]:
            if isinstance(row_data["images"], list):
                imagenes_a_procesar.extend(row_data["images"])
            else:
                imagenes_a_procesar.append(row_data["images"])

        if "imagenes" in row_data and row_data["imagenes"]:
            if isinstance(row_data["imagenes"], list):
                imagenes_a_procesar.extend(row_data["imagenes"])
            else:
                imagenes_a_procesar.append(row_data["imagenes"])

        # Unificar en el campo 'images' para consistencia
        if imagenes_a_procesar:
            row_data["images"] = imagenes_a_procesar
            # Eliminar el campo 'imagenes' para evitar duplicación
            if "imagenes" in row_data:
                del row_data["imagenes"]

        # Procesar todas las imágenes recopiladas
        if imagenes_a_procesar:
            # Crear un array con las URLs de las imágenes
            row_data["imagen_urls"] = []
            for img in imagenes_a_procesar:
                if (
                    img and len(img) > 5
                ):  # Verificar que el nombre de la imagen es válido
                    # Verificar si ya es una URL completa
                    if (
                        img.startswith("/admin/s3/")
                        or img.startswith("/static/uploads/")
                        or img.startswith("/imagenes_subidas/")
                    ):
                        # Ya es una URL completa, usar directamente
                        row_data["imagen_urls"].append(img)
                        logger.debug(f"[ADMIN_EDIT_ROW] URL completa detectada: {img}")
                    else:
                        # Intentar obtener la URL de S3 primero
                        s3_url = get_s3_url(img)
                        if s3_url:
                            row_data["imagen_urls"].append(s3_url)
                            logger.debug(
                                f"[ADMIN_EDIT_ROW] Imagen S3 encontrada: {img} -> {s3_url}"
                            )
                        else:
                            # Si no está en S3, usar la URL local
                            local_url = url_for("static", filename=f"uploads/{img}")
                            row_data["imagen_urls"].append(local_url)
                            logger.debug(
                                f"[ADMIN_EDIT_ROW] Usando URL local para imagen: {img} -> {local_url}"
                            )

            # Asignar las URLs procesadas a _imagenes para la plantilla
            if "imagen_urls" in row_data:
                row_data["_imagenes"] = row_data["imagen_urls"]
                logger.info(
                    f"[ADMIN_EDIT_ROW] Procesadas {len(row_data['imagen_urls'])} imágenes para la fila"
                )

        # Añadir información sobre la colección de origen
        catalog["collection_source"] = collection_source
        catalog["_id_str"] = str(catalog["_id"])

        if request.method == "POST":
            # Procesar campos normales y especiales
            # Inicializar updated_row con los datos existentes para preservar campos
            # no modificados
            updated_row: Dict[str, Any] = dict(row_data)
            logger.info(
                f"[ADMIN_EDIT_ROW] 🔄 Inicializando updated_row con datos existentes: {updated_row}"
            )

            for header in catalog["headers"]:
                if header == "Multimedia":
                    # Manejar campo Multimedia
                    multimedia_url = request.form.get(f"{header}_url", "").strip()
                    multimedia_file = request.files.get(f"{header}_file")

                    # Solo actualizar si se proporciona un nuevo valor
                    if multimedia_url:
                        updated_row[header] = multimedia_url
                        logger.info(
                            f"[ADMIN_EDIT_ROW] Multimedia URL actualizada: {multimedia_url}"
                        )
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

                        # Subir a S3 si está habilitado
                        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                        if use_s3:
                            try:
                                from app.utils.s3_utils import upload_file_to_s3_direct

                                logger.info(f"Subiendo multimedia a S3: {filename}")
                                # Leer el archivo y subirlo directamente a S3
                                with open(file_path, "rb") as file_obj:
                                    from werkzeug.datastructures import FileStorage

                                    file_storage = FileStorage(
                                        stream=file_obj,
                                        filename=filename,
                                        content_type="application/octet-stream",
                                    )
                                    result = upload_file_to_s3_direct(
                                        file_storage, filename
                                    )

                                if result["success"]:
                                    logger.info(
                                        f"Multimedia subida a S3: {result['url']}"
                                    )
                                    # Eliminar el archivo local después de subirlo a S3
                                    os.remove(file_path)
                                    updated_row[header] = result["url"]
                                else:
                                    logger.error(
                                        f"Error subiendo multimedia a S3: {result['error']}"
                                    )
                                    # Si falla S3, mantener local
                                    updated_row[header] = filename
                            except Exception as e:
                                logger.error(
                                    f"Error en proceso S3 para multimedia: {e}"
                                )
                                # Si falla S3, mantener local
                                updated_row[header] = filename
                        else:
                            # Almacenamiento local
                            logger.info(f"Multimedia guardada localmente: {filename}")
                            updated_row[header] = filename

                        logger.info(
                            f"[ADMIN_EDIT_ROW] Multimedia archivo actualizado: {updated_row[header]}"
                        )
                    else:
                        # Mantener valor existente si no hay cambios
                        existing_multimedia = row_data.get(header, "")
                        updated_row[header] = existing_multimedia
                        logger.info(
                            f"[ADMIN_EDIT_ROW] Multimedia existente preservado: {existing_multimedia}"
                        )

                elif header in ["Documentos", "Documentación"]:
                    # Manejar múltiples documentos por fila
                    documentos = []

                    # Obtener documentos existentes (si los hay)
                    logger.info(
                        f"[ADMIN_EDIT_ROW] 🔍 Obteniendo documentos existentes para {header}"
                    )
                    logger.info(f"[ADMIN_EDIT_ROW] 📋 row_data completo: {row_data}")
                    documentos_existentes = row_data.get(header, [])
                    logger.info(
                        f"[ADMIN_EDIT_ROW] 📄 documentos_existentes inicial: {documentos_existentes} (tipo: {type(documentos_existentes)})"
                    )

                    # Verificar el tipo de manera segura
                    if isinstance(documentos_existentes, str):
                        # Si es un string (formato antiguo), convertirlo a array
                        documentos_existentes = (
                            [documentos_existentes] if documentos_existentes else []
                        )
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🔄 Convertido string a array: {documentos_existentes}"
                        )
                    elif not hasattr(documentos_existentes, "__iter__") or isinstance(
                        documentos_existentes, str
                    ):
                        # Si no es iterable o es string, inicializar como lista vacía
                        documentos_existentes = []
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🔄 Inicializado como lista vacía: {documentos_existentes}"
                        )

                    logger.info(
                        f"[ADMIN_EDIT_ROW] 📄 documentos_existentes final: {documentos_existentes}"
                    )

                    # Obtener todos los documentos del formulario (URLs y archivos)
                    # Buscar campos con el patrón header_url_INDEX y header_file_INDEX
                    documento_urls = []
                    documento_files = []

                    # Buscar todos los campos que coincidan con el patrón
                    for key, value in request.form.items():
                        if key.startswith(f"{header}_url_") and value.strip():
                            documento_urls.append(value.strip())

                    for key, file in request.files.items():
                        if key.startswith(f"{header}_file_") and file.filename:
                            documento_files.append(file)

                    # Procesar URLs de documentos
                    for url in documento_urls:
                        if url and url.strip():
                            documentos.append(url.strip())

                    # Procesar archivos de documentos
                    for documento_file in documento_files:
                        if documento_file and documento_file.filename:
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

                            # Subir a S3 si está habilitado
                            use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                            if use_s3:
                                try:
                                    from app.utils.s3_utils import (
                                        upload_file_to_s3_direct,
                                    )

                                    logger.info(f"Subiendo documento a S3: {filename}")
                                    # Leer el archivo y subirlo directamente a S3
                                    with open(file_path, "rb") as file_obj:
                                        from werkzeug.datastructures import FileStorage

                                        file_storage = FileStorage(
                                            stream=file_obj,
                                            filename=filename,
                                            content_type="application/octet-stream",
                                        )
                                        result = upload_file_to_s3_direct(
                                            file_storage, filename
                                        )

                                    if result["success"]:
                                        logger.info(
                                            f"Documento subido a S3: {result['url']}"
                                        )
                                        # Eliminar el archivo local después de subirlo a
                                        # S3
                                        os.remove(file_path)
                                        documentos.append(result["url"])
                                    else:
                                        logger.error(
                                            f"Error subiendo documento a S3: {result['error']}"
                                        )
                                        # Si falla S3, mantener local
                                        documentos.append(filename)
                                except Exception as e:
                                    logger.error(
                                        f"Error en proceso S3 para documento: {e}"
                                    )
                                    # Si falla S3, mantener local
                                    documentos.append(filename)
                            else:
                                # Almacenamiento local
                                logger.info(
                                    f"Documento guardado localmente: {filename}"
                                )
                                documentos.append(filename)

                    # Combinar documentos existentes con los nuevos
                    logger.info(
                        f"[ADMIN_EDIT_ROW] {header} - Documentos existentes: {documentos_existentes}"
                    )
                    logger.info(
                        f"[ADMIN_EDIT_ROW] {header} - Documentos nuevos: {documentos}"
                    )

                    if documentos_existentes and documentos:
                        # Hay documentos existentes Y nuevos: combinar
                        documentos = documentos_existentes + documentos
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} - Combinando existentes + nuevos: {documentos}"
                        )
                    elif documentos_existentes and not documentos:
                        # Hay documentos existentes pero NO nuevos: preservar existentes
                        documentos = documentos_existentes
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} - Preservando existentes: {documentos}"
                        )
                    else:
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} - Sin documentos existentes ni nuevos: {documentos}"
                        )
                    # Si no hay documentos existentes ni nuevos, mantener lista vacía

                    # Almacenar como array de documentos con nombre único basado en el índice de la columna
                    # Encontrar el índice de esta columna específica
                    header_index = None
                    for i, h in enumerate(catalog.get("headers", [])):
                        if h == header:
                            if header_index is None:
                                header_index = i
                            else:
                                # Si ya encontramos una columna con este nombre, usar el
                                # índice actual
                                header_index = i
                                break

                    # Usar el header original para mantener consistencia
                    # El unique_header solo se usa internamente, pero almacenamos con el
                    # header original
                    updated_row[header] = documentos
                    logger.info(
                        f"[ADMIN_EDIT_ROW] {header} documentos finales almacenados: {documentos}"
                    )
                else:
                    # Campo normal - verificar si es un campo de archivo
                    field_value = request.form.get(header, "")

                    # Verificar si hay un archivo nuevo para este campo
                    file_field = request.files.get(f"{header}_file")

                    if file_field and file_field.filename:
                        # Hay un archivo nuevo, procesarlo
                        import uuid  # noqa: I001

                        from werkzeug.utils import secure_filename

                        from app.routes.catalogs_routes import get_upload_dir

                        filename = secure_filename(
                            f"{uuid.uuid4().hex}_{file_field.filename}"
                        )
                        upload_dir = get_upload_dir()
                        file_path = os.path.join(upload_dir, filename)
                        file_field.save(file_path)

                        # Subir a S3 si está habilitado
                        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                        if use_s3:
                            try:
                                from app.utils.s3_utils import upload_file_to_s3_direct

                                logger.info(f"Subiendo archivo a S3: {filename}")
                                # Leer el archivo y subirlo directamente a S3
                                with open(file_path, "rb") as file_obj:
                                    from werkzeug.datastructures import FileStorage

                                    file_storage = FileStorage(
                                        stream=file_obj,
                                        filename=filename,
                                        content_type=(
                                            "image/jpeg"
                                            if header.lower() in ["imagen", "imagenes"]
                                            else "application/octet-stream"
                                        ),
                                    )
                                    result = upload_file_to_s3_direct(
                                        file_storage, filename
                                    )

                                if result["success"]:
                                    logger.info(f"Archivo subido a S3: {result['url']}")
                                    # Eliminar el archivo local después de subirlo a S3
                                    os.remove(file_path)
                                    updated_row[header] = result["url"]
                                else:
                                    logger.error(
                                        f"Error subiendo archivo a S3: {result['error']}"
                                    )
                                    # Si falla S3, mantener local
                                    updated_row[header] = filename
                            except Exception as e:
                                logger.error(f"Error en proceso S3 para archivo: {e}")
                                # Si falla S3, mantener local
                                updated_row[header] = filename
                        else:
                            # Almacenamiento local
                            logger.info(f"Archivo guardado localmente: {filename}")
                            updated_row[header] = filename

                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} archivo actualizado: {updated_row[header]}"
                        )
                    elif field_value:
                        # Hay un valor de URL/texto nuevo
                        updated_row[header] = field_value
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} valor actualizado: {field_value}"
                        )
                    else:
                        # No hay valor nuevo, preservar el existente
                        existing_value = row_data.get(header, "")
                        updated_row[header] = existing_value
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} valor existente preservado: {existing_value}"
                        )

            # Manejar eliminación de documentos y multimedia
            deleted_documents = request.form.get("deleted_documents", "")
            deleted_multimedia = request.form.get("deleted_multimedia", "")

            if deleted_documents:
                try:
                    import json

                    deleted_docs = json.loads(deleted_documents)
                    for deleted_doc in deleted_docs:
                        header = deleted_doc.get("header")
                        value = deleted_doc.get("value")
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🗑️ Procesando documento eliminado - Header: {header}, Value: {value}"
                        )
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 📋 Estado actual de updated_row[{header}]: {updated_row.get(header)}"
                        )

                        if header in updated_row and updated_row[header]:
                            if hasattr(
                                updated_row[header], "__iter__"
                            ) and not isinstance(updated_row[header], str):
                                # Es una lista/array, remover de la lista
                                original_count = len(updated_row[header])
                                updated_row[header] = [
                                    doc for doc in updated_row[header] if doc != value
                                ]
                                new_count = len(updated_row[header])
                                logger.info(
                                    f"[ADMIN_EDIT_ROW] ✅ Documento eliminado de lista - Original: {original_count}, Nuevo: {new_count}"
                                )
                                # Si queda vacía, mantener como lista vacía
                                if not updated_row[header]:
                                    updated_row[header] = []
                            else:
                                # Si es un valor único, eliminar la clave
                                if updated_row[header] == value:
                                    updated_row[header] = ""
                                    logger.info(
                                        f"[ADMIN_EDIT_ROW] ✅ Documento único eliminado: {header}"
                                    )
                                else:
                                    logger.warning(
                                        f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar documento único - Valor no coincide: {updated_row[header]} != {value}"
                                    )
                        else:
                            logger.warning(
                                f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar documento - Header no encontrado o vacío: {header}"
                            )
                    logger.info(
                        f"[ADMIN_EDIT_ROW] Documentos eliminados: {deleted_docs}"
                    )
                except Exception as e:
                    logger.error(
                        f"[ADMIN_EDIT_ROW] Error procesando documentos eliminados: {e}"
                    )

            if deleted_multimedia:
                try:
                    import json

                    deleted_media = json.loads(deleted_multimedia)
                    logger.info(
                        f"[ADMIN_EDIT_ROW] 🗑️  Procesando multimedia eliminado: {deleted_media}"
                    )
                    logger.info(
                        f"[ADMIN_EDIT_ROW] 📋 Estado de updated_row antes de eliminar multimedia: {updated_row}"
                    )

                    for deleted_item in deleted_media:
                        header = deleted_item.get("header")
                        value = deleted_item.get("value")
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🎯 Eliminando multimedia - Header: {header}, Value: {value}"
                        )
                        if header in updated_row and updated_row[header] == value:
                            updated_row[header] = ""
                            logger.info(
                                f"[ADMIN_EDIT_ROW] ✅ Multimedia eliminado correctamente: {header}"
                            )
                        else:
                            logger.warning(
                                f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar multimedia - Header: {header}, Value: {value}, Current: {updated_row.get(header)}"
                            )

                    logger.info(
                        f"[ADMIN_EDIT_ROW] 📋 Estado de updated_row después de eliminar multimedia: {updated_row}"
                    )
                except Exception as e:
                    logger.error(
                        f"[ADMIN_EDIT_ROW] ❌ Error procesando multimedia eliminado: {e}"
                    )

            # Manejo de imágenes (mantener compatibilidad)
            if "images" in request.files:
                files = request.files.getlist("images")
                from app.routes.catalogs_routes import (  # noqa: I001
                    allowed_image,
                    get_upload_dir,
                )

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

                        # Subir a S3 si está habilitado
                        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                        if use_s3:
                            try:
                                from app.utils.s3_utils import upload_file_to_s3_direct

                                logger.info(f"Subiendo imagen a S3: {filename}")
                                # Leer el archivo y subirlo directamente a S3
                                with open(file_path, "rb") as file_obj:
                                    from werkzeug.datastructures import FileStorage

                                    file_storage = FileStorage(
                                        stream=file_obj,
                                        filename=filename,
                                        content_type="image/jpeg",
                                    )
                                    result = upload_file_to_s3_direct(
                                        file_storage, filename
                                    )

                                if result["success"]:
                                    logger.info(f"Imagen subida a S3: {result['url']}")
                                    # Eliminar el archivo local después de subirlo a S3
                                    os.remove(file_path)
                                    nuevas_imagenes.append(result["url"])
                                else:
                                    logger.error(
                                        f"Error subiendo imagen a S3: {result['error']}"
                                    )
                                    # Si falla S3, mantener local
                                    nuevas_imagenes.append(filename)
                            except Exception as e:
                                logger.error(f"Error en proceso S3 para imagen: {e}")
                                # Si falla S3, mantener local
                                nuevas_imagenes.append(filename)
                        else:
                            # Almacenamiento local
                            nuevas_imagenes.append(filename)
                if nuevas_imagenes:
                    existing_images = updated_row.get("images", [])
                    if isinstance(existing_images, list):
                        updated_row["images"] = existing_images + nuevas_imagenes
                    else:
                        updated_row["images"] = nuevas_imagenes

            # Eliminar imágenes seleccionadas
            delete_images = request.form.getlist("delete_images")
            if delete_images:
                current_images = updated_row.get("images", [])
                if isinstance(current_images, list):
                    updated_row["images"] = [
                        img for img in current_images if img not in delete_images
                    ]
                else:
                    updated_row["images"] = []
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
            try:
                catalog = collection.find_one({"_id": ObjectId(catalog_id)})
                if catalog:
                    break
            except Exception as e:
                current_app.logger.warning(
                    f"Error buscando en colección {collection_name}: {str(e)}"
                )
                continue

        if not catalog:
            return jsonify({"error": "Catálogo no encontrado"}), 404

        # Extraer imágenes de las filas del catálogo
        images = []
        data_to_search = get_catalog_rows(catalog)

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
        import traceback

        current_app.logger.error(f"Traceback completo: {traceback.format_exc()}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500


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
                error_msg = f"Error eliminando {catalog_id}: {str(e)}"  # type: ignore
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
                # Convertir bytes a string si es posible, o a una representación en
                # base64
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
last_ops: dict[str, int] = {}  # type: ignore
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
        app.register_blueprint(admin_system_bp)
        app.register_blueprint(admin_s3_bp)
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
        success = monitoring.check_database_health(client)  # type: ignore

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


@admin_bp.route("/generate-presigned-url")
def generate_presigned_url_route():
    """
    Genera una URL firmada para un archivo en S3.
    """
    try:
        # Obtener parámetros de la request
        file_url = request.args.get("file_url")
        expiration = request.args.get(
            "expiration", 3600, type=int
        )  # 1 hora por defecto

        if not file_url:
            return jsonify({"error": "file_url es requerido"}), 400

        # Extraer bucket y key de la URL de S3
        # Ejemplo: https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/archivo.pdf
        current_app.logger.info(f"[DEBUG] Validando URL: {file_url}")
        current_app.logger.info(f"[DEBUG] Longitud de URL: {len(file_url)}")
        current_app.logger.info(
            f"[DEBUG] 's3.amazonaws.com' in file_url: {'s3.amazonaws.com' in file_url}"
        )
        current_app.logger.info(
            f"[DEBUG] 'edf-catalogo-tablas.s3' in file_url: {'edf-catalogo-tablas.s3' in file_url}"
        )
        current_app.logger.info(
            f"[DEBUG] URL starts with https://: {file_url.startswith('https://')}"
        )
        current_app.logger.info(f"[DEBUG] '.s3.' in file_url: {'.s3.' in file_url}")

        # Validación más robusta para URLs de S3
        # Verificar si es una URL de S3 válida
        is_s3_url = (
            "s3.amazonaws.com" in file_url
            or "edf-catalogo-tablas.s3" in file_url
            or file_url.startswith("https://")
            and ".s3." in file_url
        )

        if is_s3_url:
            # Extraer el nombre del archivo de la URL
            file_name = file_url.split("/")[-1]
            bucket_name = current_app.config.get(
                "S3_BUCKET_NAME", "edf-catalogo-tablas"
            )

            current_app.logger.info(
                f"[DEBUG] Archivo: {file_name}, Bucket: {bucket_name}"
            )

            # Generar URL firmada
            presigned_url = get_s3_url(file_name, expiration)

            if presigned_url:
                current_app.logger.info(
                    f"[DEBUG] URL firmada generada: {presigned_url[:100]}..."
                )
                return jsonify(
                    {
                        "success": True,
                        "presigned_url": presigned_url,
                        "expiration": expiration,
                    }
                )
            else:
                current_app.logger.error("[DEBUG] get_s3_url devolvió None")
                return jsonify({"error": "No se pudo generar la URL firmada"}), 500
        else:
            current_app.logger.error(f"[DEBUG] URL no reconocida como S3: {file_url}")
            return jsonify({"error": "URL no es de S3"}), 400

    except Exception as e:
        current_app.logger.error(f"Error generando URL firmada: {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/serve-local-file/<path:filename>")
def serve_local_file(filename):
    """
    Sirve archivos locales desde el directorio de uploads.
    """
    try:
        from app.routes.catalogs_routes import get_upload_dir

        upload_dir = get_upload_dir()
        file_path = os.path.join(upload_dir, filename)

        if not os.path.exists(file_path):
            return "Archivo no encontrado", 404

        # Determinar MIME type basado en extensión
        mime_type = "application/octet-stream"
        if filename.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename.lower().endswith((".md", ".markdown")):
            mime_type = "text/markdown"
        elif filename.lower().endswith(".txt"):
            mime_type = "text/plain"
        elif filename.lower().endswith((".doc", ".docx")):
            mime_type = "application/msword"

        return send_file(file_path, as_attachment=False, mimetype=mime_type)

    except Exception as e:
        current_app.logger.error(f"Error sirviendo archivo local: {e}")
        return "Error sirviendo archivo", 500


# Ruta temporal de PDF eliminada - ahora se usan archivos locales


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
