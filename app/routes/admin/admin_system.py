# Script: admin_system.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_system.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Rutas de gestión y monitoreo de sistemas para la funcionalidad de administración.
"""
import logging
import os
import platform
from datetime import datetime

import psutil
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.cache_system import get_cache_stats
from app.monitoring import check_system_health, get_health_status
from app.routes.maintenance_routes import admin_required
from app.routes.temp_files_utils import delete_temp_files, list_temp_files

admin_system_bp = Blueprint("admin_system", __name__, url_prefix="/admin/system")
logger = logging.getLogger(__name__)


def get_system_status_data(full=False):
    """
    Obtiene datos del estado del sistema.
    """
    try:
        # Obtener informe completo de estado
        health_report = check_system_health()
        # Obtener estadísticas de solicitudes
        health_status = get_health_status()
        metrics = health_status.get("metrics", {})
        request_stats = metrics.get("request_stats", {})

        # Calcular uptime
        start_time = datetime.strptime(
            metrics.get("start_time", ""), "%Y-%m-%d %H:%M:%S"
        )
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

        status_data = {
            "health": health_report,
            "uptime": uptime_str,
            "request_stats": request_stats,
            "database": metrics.get("database_status", {}),
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

    except Exception as e:
        logger.error("Error en get_system_status_data: %s", str(e), exc_info=True)
        return {
            "health": {"status": "error", "metrics": {}},
            "uptime": "Error",
            "request_stats": {"total_requests": 0},
            "database": {"is_available": False, "response_time_ms": 0},
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory": {},
            "temp_files": [],
        }


@admin_system_bp.route("/status")
@admin_required
def system_status():
    """
    Muestra el estado del sistema.
    """
    try:
        # Obtener datos del sistema
        data = get_system_status_data()

        # Obtener la lista de archivos de log
        logs_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../logs")
        )
        log_files = get_log_files(logs_dir)

        # Obtener la lista de archivos de backup
        backup_dir = os.path.abspath(os.path.join(os.getcwd(), "backups"))
        backup_files = get_backup_files(backup_dir)

        # Pasar cache_stats y temp_files como variables independientes para el template
        cache_stats = data.get("cache_stats")
        temp_files = data.get("temp_files")

        return render_template(
            "admin/system_status.html",
            data=data,
            log_files=log_files,
            backup_files=backup_files,
            cache_stats=cache_stats,
            temp_files=temp_files,
        )
    except Exception as e:
        logger.error("Error en system_status: %s", str(e), exc_info=True)
        flash("Error al obtener el estado del sistema", "danger")
        return redirect(url_for("admin.dashboard_admin"))


@admin_system_bp.route("/status/report")
@admin_required
def system_status_report():
    """
    Genera un reporte del estado del sistema en formato JSON.
    """
    data = get_system_status_data(full=True)
    response = current_app.response_class(
        response=jsonify(data), mimetype="application/json"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=system_status_report.json"
    )
    return response


@admin_system_bp.route("/delete-temp-files", methods=["POST"])
@admin_required
def delete_temp_files_route():
    """
    Elimina archivos temporales seleccionados.
    """
    selected = request.form.getlist("temp_files")
    if not selected:
        flash("No se seleccionaron archivos para borrar", "warning")
        return redirect(url_for("admin.system_status"))
    removed = delete_temp_files(selected)
    flash(f"Archivos temporales eliminados: {removed}", "success")
    return redirect(url_for("admin.system_status"))


def get_log_files(logs_dir):
    """
    Obtiene la lista de archivos de log disponibles.
    """
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

    except Exception as e:
        logger.error("Error al obtener archivos de log: %s", str(e), exc_info=True)
        return []


def get_backup_files(backup_dir):
    """
    Obtiene la lista de archivos de backup disponibles.
    """
    try:
        logger.info("Buscando archivos de backup en: %s", backup_dir)
        if not os.path.exists(backup_dir):
            logger.warning("El directorio de backups no existe: %s", backup_dir)
            os.makedirs(backup_dir, exist_ok=True)
            logger.info("Directorio de backups creado: %s", backup_dir)
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

    except Exception as e:
        logger.error("Error al obtener archivos de backup: %s", str(e), exc_info=True)
        return []
