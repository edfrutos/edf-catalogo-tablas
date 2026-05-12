# Script: admin_maintenance_routes.py
# Descripción: Rutas administrativas pequeñas de mantenimiento.
# Autor: EDF Developer

import logging
import os
import re
from datetime import datetime

from flask import flash, jsonify, redirect, render_template, request, url_for

from app.audit import audit_log
from app.decorators import admin_required
from app.routes.temp_files_utils import delete_temp_files
from app.database import get_reset_tokens_collection
import app.monitoring as monitoring


logger = logging.getLogger(__name__)


def register_admin_maintenance_routes(admin_bp) -> None:
    """Registra rutas pequeñas de mantenimiento sobre el blueprint admin."""

    @admin_bp.route("/reset_gdrive_token", methods=["POST"])
    @admin_required
    def reset_gdrive_token_route():
        import subprocess
        import sys

        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "../../../tools/db_utils/google_drive_utils.py"
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
        script_path = os.path.join(os.path.dirname(__file__), "../../../tools/log_utils.py")
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
                os.path.join(os.path.dirname(__file__), "../../../logs")
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
