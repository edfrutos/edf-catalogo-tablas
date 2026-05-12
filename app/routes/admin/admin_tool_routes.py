# Script: admin_tool_routes.py
# Descripción: Rutas administrativas auxiliares de herramientas y ficheros.
# Autor: EDF Developer

import logging
import os
from flask import current_app, jsonify, render_template, request, send_file

from app.decorators import admin_required
from app.routes.s3_utils import get_s3_url


logger = logging.getLogger(__name__)


def register_admin_tooloutes(admin_bp) -> None:
    """Registra rutas administrativas auxiliares sobre el blueprint admin."""

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
