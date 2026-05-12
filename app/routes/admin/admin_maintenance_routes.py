# Script: admin_maintenance_routes.py
# Descripción: Rutas administrativas pequeñas de mantenimiento.
# Autor: EDF Developer

import os

from flask import flash, jsonify, redirect, render_template, request, url_for

from app.decorators import admin_required


def register_admin_maintenance_routes(admin_bp) -> None:
    """Registra rutas pequeñas de mantenimiento sobre el blueprint admin."""

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
