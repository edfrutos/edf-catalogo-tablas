# app/uploads_routes.py
import os
import tempfile
import zipfile

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app import app, s3_client  # type: ignore
from app.models import S3_BUCKET_NAME  # type: ignore
from app.utils import (
    allowed_file,  # type: ignore
    eliminar_archivo_imagen,  # type: ignore
    get_s3_url,  # type: ignore
    upload_file_to_s3,  # type: ignore
)

uploads_bp = Blueprint("uploads", __name__)

# -------------------------------------------
# RUTA PARA CARGAR ARCHIVOS (Imágenes)
# -------------------------------------------


@uploads_bp.route("/upload_image", methods=["POST"])
def upload_image():
    if "usuario" not in session:
        flash("Debes iniciar sesión.", "error")
        return redirect(url_for("auth.login"))

    file = request.files.get("file")
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Subir a S3
        with open(filepath, "rb") as f:
            if upload_file_to_s3(f, S3_BUCKET_NAME, filename):
                flash("Imagen subida correctamente.", "success")
            else:
                flash("Error al subir imagen a S3.", "error")

        return redirect(url_for("main.home"))

    flash("Archivo no válido o no seleccionado.", "error")
    return redirect(url_for("main.home"))


# -------------------------------------------
# RUTA PARA DESCARGAR EXCEL + IMÁGENES COMO ZIP
# -------------------------------------------


@uploads_bp.route("/descargar-catalogo")
def descargar_catalogo():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    from app.utils import get_current_spreadsheet, leer_datos_excel  # type: ignore

    spreadsheet_path = get_current_spreadsheet()
    if not spreadsheet_path or not os.path.exists(spreadsheet_path):
        return "No hay archivo Excel para descargar.", 404

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(temp_zip.name, "w") as zf:
        zf.write(spreadsheet_path, arcname=os.path.basename(spreadsheet_path))

        data = leer_datos_excel(spreadsheet_path)
        image_paths = set()

        for row in data:
            imagenes = row.get("Imagenes", [])
            if isinstance(imagenes, str):
                imagenes = imagenes.split(", ")

            for ruta in imagenes:
                if ruta and ruta.startswith("s3://"):
                    try:
                        s3_parts = ruta[5:].split("/", 1)
                        if len(s3_parts) == 2:
                            bucket_name, object_key = s3_parts
                            if bucket_name == S3_BUCKET_NAME:
                                temp_img = os.path.join(
                                    tempfile.gettempdir(), os.path.basename(object_key)
                                )
                                s3_client.download_file(
                                    S3_BUCKET_NAME, object_key, temp_img
                                )
                                image_paths.add(temp_img)
                    except Exception as e:
                        app.logger.error(f"Error descargando imagen S3: {str(e)}")

        for img_path in image_paths:
            arcname = os.path.join("imagenes", os.path.basename(img_path))
            zf.write(img_path, arcname=arcname)

    return send_from_directory(
        directory=os.path.dirname(temp_zip.name),
                               path=os.path.basename(temp_zip.name),
                               as_attachment=True,
        download_name="catalogo.zip",
    )


# -------------------------------------------
# SERVIR IMÁGENES DESDE S3 O LOCAL
# -------------------------------------------


@uploads_bp.route("/imagenes/<filename>")
def serve_image(filename):
    s3_param = request.args.get("s3")
    if s3_param == "true":
        url = get_s3_url(filename)
        if url:
            return redirect(url)
        else:
            return "No se pudo generar URL de acceso.", 404

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
