# Script: admin_backups.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_backups.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Backup management routes for admin functionality.
"""
import csv
import gzip
import io
import json
import logging
import os
from datetime import datetime

from bson import ObjectId
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app.audit import audit_log
from app.database import get_catalogs_collection, get_mongo_client
from app.decorators import admin_required
from tools.db_utils.google_drive_utils import upload_to_drive

admin_backups_bp = Blueprint("admin_backups", __name__, url_prefix="/admin/backups")
logger = logging.getLogger(__name__)


def get_backup_dir():
    """Obtiene el directorio de respaldos, asegurando que exista"""
    backup_dir = os.path.abspath(os.path.join(os.getcwd(), "backups"))
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


@admin_backups_bp.route("/json")
@admin_required
def backup_json():
    """
    Crea un backup en formato JSON de los catálogos.
    """
    catalog = get_catalogs_collection()
    if catalog is None:
        flash("Error: No se pudo acceder a la colección de catálogos", "error")
        return redirect(url_for("maintenance.maintenance_dashboard"))

    data = list(catalog.find())
    for d in data:
        d["_id"] = str(d["_id"])

    output = json.dumps(data, indent=4, default=str)

    # Guardar el archivo en /backups/ con nombre único
    backups_dir = get_backup_dir()
    filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = os.path.join(backups_dir, filename)

    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output)

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
    except Exception as e:
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

    # Permitir descarga directa
    return send_file(
        io.BytesIO(output.encode()),
        download_name="backup_catalog.json",
        as_attachment=True,
    )


@admin_backups_bp.route("/csv")
@admin_required
def backup_csv():
    """
    Crea un backup en formato CSV de los catálogos.
    """
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
    backups_dir = get_backup_dir()
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
    except Exception as e:
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

    # Permitir descarga directa
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        download_name="backup_catalog.csv",
        as_attachment=True,
    )


@admin_backups_bp.route("/cleanup", methods=["POST"])
@admin_required
def cleanup_old_backups():
    """
    Elimina backups antiguos según la fecha o cantidad máxima permitida.
    """
    days = int(request.form.get("days", 30))
    max_files = int(request.form.get("max_files", 20))
    backups_dir = get_backup_dir()

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
        if (now - mtime).days > days:
            try:
                os.remove(f)
                removed += 1
                logger.info("Backup eliminado por antigüedad: %s", f)
            except Exception as e:
                logger.error("Error al eliminar backup %s: %s", f, e)

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
                logger.info("Backup eliminado por exceso de cantidad: %s", f)
            except Exception as e:
                logger.error("Error al eliminar backup %s: %s", f, e)

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


@admin_backups_bp.route("/list", methods=["GET", "POST"])
@admin_required
def backups_list():
    """
    Lista todos los backups disponibles.
    """
    backups_dir = get_backup_dir()
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
                except Exception as e:
                    flash(f"Error al eliminar el backup: {str(e)}", "danger")
            else:
                flash("El archivo no existe", "warning")
        else:
            flash("Nombre de archivo no válido", "danger")
        return redirect(url_for("admin.backups_list"))

    return render_template("admin/backups_list.html", backup_files=backup_files)


@admin_backups_bp.route("/download/<filename>")
@admin_required
def download_backup(filename):
    """
    Descarga un archivo de backup específico.
    """
    backups_dir = get_backup_dir()
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
