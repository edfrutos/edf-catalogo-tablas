# Script: admin_backup_routes.py
# Descripción: Rutas pequeñas de backup administrativo registradas sobre admin_bp.
# Autor: EDF Developer

import csv
import io
import json
import logging
import traceback
import os
import requests
import shutil
from datetime import datetime
from typing import Any, Dict

from flask import current_app, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from app.audit import audit_log
from app.database import (
    get_audit_logs_collection,
    get_catalogs_collection,
    get_mongo_db,
)
from flask_login import current_user
from app.decorators import admin_required
from app.routes.admin.admin_backup_utils import get_backup_dir, get_backup_files
from app.routes.admin.admin_backup_restore_utils import (
    BackupRestoreError,
    is_mongodb_binary_dump_name,
    prepare_restore_documents,
    read_backup_json_file,
)
from tools.db_utils.google_drive_utils import upload_to_drive
from tools.db_utils.google_drive_utils import list_files_in_folder


logger = logging.getLogger(__name__)


def backup_log_action(
    action: str,
    message: str,
    details: dict | None = None,
    user_id: str | None = None,
    collection: str | None = None,
) -> None:
    """Registra acciones administrativas de backup sin depender de admin_routes.py."""
    try:
        if not user_id and hasattr(current_user, "id"):
            user_id = str(current_user.id)

        log_entry = {
            "action": action,
            "message": message,
            "details": details or {},
            "user_id": user_id,
            "collection": collection,
            "timestamp": datetime.utcnow(),
            "source": "admin_backup_routes",
        }

        audit_logs = get_audit_logs_collection()
        if audit_logs is not None:
            audit_logs.insert_one(log_entry)

        logger.info("[AUDIT][BACKUP] %s: %s", action, message)

    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error al registrar auditoría de backup: %s", str(e), exc_info=True)



def register_admin_backup_routes(admin_bp) -> None:
    """Registra rutas de backup sobre el blueprint admin existente."""

    @admin_bp.route("/backup/json")
    @admin_required
    def backup_json():
        catalog = get_catalogs_collection()
        if catalog is None:
            flash("Error: No se pudo acceder a la colección de catálogos", "error")
            return redirect(url_for("maintenance.maintenance_daard"))

        data = list(catalog.find())
        for d in data:
            d["_id"] = str(d["_id"])

        output = io.StringIO()
        json.dump(data, output, indent=4, default=str)
        output.seek(0)

        backups_dir = get_backup_dir()
        filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backups_dir, filename)

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())

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

        return send_file(
            io.BytesIO(output.read().encode()),
            download_name="backup_catalog.json",
            as_attachment=True,
        )

    @admin_bp.route("/backup/csv")
    @admin_required
    def backup_csv():
        catalog = get_catalogs_collection()
        if catalog is None:
            flash("Error: No se pudo acceder a la colección de catálogos", "error")
            return redirect(url_for("maintenance.maintenance_dashboard"))

        data = list(catalog.find())
        if not data:
            flash("No hay datos para exportar", "warning")
            return redirect(url_for("maintenance.maintenance_dashboard"))

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

        backups_dir = get_backup_dir()
        filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        backup_path = os.path.join(backups_dir, filename)

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())

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

        return send_file(
            io.BytesIO(output.read().encode()),
            download_name="backup_catalog.csv",
            as_attachment=True,
        )

    @admin_bp.route("/backups/cleanup", methods=["POST"])
    @admin_required
    def cleanup_old_backups():
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

        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        now = datetime.now()
        removed = 0

        for f in files:
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if (now - mtime).days > days:
                try:
                    os.remove(f)
                    removed += 1
                except (OSError, PermissionError):
                    pass

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
                except (OSError, PermissionError):
                    pass

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
                    # Validar el nombre del archivo para evitar ataques de traversal de
                    # directorio
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
            # En lugar de redirigir, mostrar la página de Google Drive con un mensaje
            # de error
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

            # Verificar que es un archivo de backup válido (usar la misma lógica que
            # get_backup_files)
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

        # Agregar la ruta de tools/db_utils al path (compatible con aplicaciones
        # empaquetadas)
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
            from google_drive_utils import (
                # pyright: ignore[reportMissingModuleSource]
                upload_file_to_drive as upload_to_drive,
            )
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
            result = upload_to_drive(file_path, "Backups_CatalogoTablas")

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
                    backup_log_action(
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
                    backup_log_action(
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

                    # Si falla la eliminación local, la subida a Drive fue exitosa, así que
                    # lo consideramos un éxito parcial
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
                backup_log_action(
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
            backup_log_action(
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

            # Obtener la ruta del archivo de backup
            backup_dir = get_backup_dir()
            file_path = os.path.join(backup_dir, filename)

            if is_mongodb_binary_dump_name(filename):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Este archivo es un backup binario de MongoDB (mongodump). Solo se pueden restaurar backups en formato JSON. Use el archivo backup_*.json.gz en su lugar.",
                        }
                    ),
                    400,
                )

            try:
                backup_data = read_backup_json_file(file_path)
                processed_docs = prepare_restore_documents(backup_data)
            except BackupRestoreError as restore_error:
                current_app.logger.error(
                    f"Error procesando backup local {filename}: {str(restore_error)}"
                )
                return jsonify({"success": False, "error": str(restore_error)}), 400

            current_app.logger.info(
                f"Backup local preparado para restauración: {filename}, documentos: {len(processed_docs)}"
            )

            # Obtener la colección de catálogos
            catalog_collection = get_catalogs_collection()
            if catalog_collection is None:
                return (
                    jsonify(
                        {"success": False, "error": "No se pudo acceder a la base de datos"}
                    ),
                    500,
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
            _ = request.form.get("download_url")

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
            import tempfile

            # Descargar el archivo desde Google Drive usando la API
            from tools.db_utils.google_drive_utils import download_file

            # Obtener el file_id del backup_id, que es el mismo en este caso
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
                current_app.logger.info(f"Procesando archivo temporal: {temp_path}")

                try:
                    backup_data = read_backup_json_file(temp_path)
                    processed_docs = prepare_restore_documents(backup_data)
                except BackupRestoreError as restore_error:
                    current_app.logger.error(
                        f"Error procesando backup de Google Drive {backup_id}: {str(restore_error)}"
                    )
                    return jsonify({"success": False, "error": str(restore_error)}), 400

                current_app.logger.info(
                    f"Backup de Google Drive preparado para restauración: {backup_id}, documentos: {len(processed_docs)}"
                )

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

                        # Eliminar archivos binarios antiguos (mantener solo los 5 más
                        # recientes)
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

                        # Eliminar archivos JSON antiguos (mantener solo los 5 más
                        # recientes)
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

                                            # Crear datetime usando la hora local (como se
                                            # generó originalmente)
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
