# Script: admin_backup_routes.py
# Descripción: Rutas pequeñas de backup administrativo registradas sobre admin_bp.
# Autor: EDF Developer

import csv
import io
import json
import logging
import os
from datetime import datetime

from flask import current_app, flash, jsonify, redirect, render_template, request, send_file, session, url_for

from app.audit import audit_log
from app.database import get_catalogs_collection
from app.decorators import admin_required
from app.routes.admin.admin_backup_utils import get_backup_dir, get_backup_files
from tools.db_utils.google_drive_utils import upload_to_drive
from tools.db_utils.google_drive_utils import list_files_in_folder


logger = logging.getLogger(__name__)


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
