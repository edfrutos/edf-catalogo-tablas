# Script: admin_s3.py
# Descripción: Rutas administrativas para servir archivos S3 mediante proxy.
# Autor: EDF Developer

import mimetypes
import os

import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, Response, current_app, jsonify, send_file, send_from_directory

admin_s3_bp = Blueprint("admin_s3", __name__, url_prefix="/admin")


def serve_s3_file(filename: str):
    """
    Sirve un archivo desde S3 como proxy para evitar problemas CORS.

    Args:
        filename (str): Nombre del archivo en S3.

    Returns:
        Flask response.
    """
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            region_name=current_app.config.get("AWS_DEFAULT_REGION", "eu-central-1"),
        )

        response = s3_client.get_object(
            Bucket=current_ap.config.get("S3_BUCKET_NAME"),
            Key=filename,
        )

        file_content = response["Body"].read()
        content_type = response.get("ContentType", "application/octet-stream")

        return Response(
            file_content,
            mimetype=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )

    except ClientError as e:
        current_app.logger.error(f"Error descargando archivo S3 {filename}: {e}")

        uploads_dir = current_app.config.get("UPLOAD_FOLDER")
        if not uploads_dir:
            uploads_dir = os.path.join(current_app.root_path, "static", "uploads")

        safe_filename = os.path.basename(filename)
        local_path = os.path.join(uploads_dir, safe_filename)

        current_app.logger.info(
            f"[S3-PROXY] Archivo no encontrado en S3, buscando fallback local físico: {lcal_path}"
        )

        if os.path.exists(local_path):
            current_app.logger.info(f"[S3-PROXY] Archivo local encontrado: {local_path}")
            return send_from_directory(
                uploads_dir,
                safe_filename,
                as_attachment=False,
            )

        current_app.logger.error(
            f"[S3-PROXY] Archivo no encontrado ni en S3 ni localmente: {safe_filename}"
        )

        return {
            "error": "Archivo no encontrado en S3 ni localmente",
            "filename": safe_filename,
            "local_path_checked": local_path,
        }, 404

    except Exception as e:
        current_app.logger.error(
            f"Error inesperado sirviendo archivo S3 {filename}: {e}"
        )
        return jsonify({"error": "Error interno del servidor"}), 500


@admin_s3_bp.route("/s3/<path:filename>")
def serve_s3_proxy(filename):
    """
    Ruta para servir archivos S3 como proxy.
    Evita problemas CORS al descargar archivos desde S3.
    """
    current_app.logger.info(f"[S3-PROXY] Solicitud para archivo: {filename}")

    try:
        aws_key = current_app.config.get("AWS_ACCESS_KEY_ID")
        aws_secret = current_app.config.get("AWS_SECRET_ACCESS_KEY")
        aws_region = current_app.config.get("AWS_REGION", "eu-central-1")
        aws_bucket = current_app.config.get("S3_BUCKET_NAME")

        current_app.logger.info(
            f"[S3-PROXY] Config S3 - Key: {'OK' if aws_key else 'NO'}, "
            f"Secret: {'OK' if aws_secret else 'NO'}, Region: {aws_region}, Bucket: {aws_bucket}"
        )

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=aws_region,
        )

        current_app.logger.info(
            f"[S3-PROXY] Descargando archivo desde S3: Bucket={aws_bucket}, Key={filename}"
        )

        response = s3_client.get_object(Bucket=aws_bucket, Key=filename)

        file_content = response["Body"].read()
        content_type = response.get("ContentType", "application/octet-stream")

        if filename.lower().endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.lower().endswith(".txt"):
            content_type = "text/plain"
        elif filename.lower().endswith(".md"):
            content_type = "text/markdown"

        current_app.logger.info(
            f"[S3-PROXY] Archivo descargado exitosamente - "
            f"Tamaño: {len(file_content)} bytes, Tipo: {content_type}"
        )

        return Response(
            file_content,
            mimetype=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )

    except ClientError as e:
        current_app.logger.error(f"Error descargando archivo S3 {filename}: {e}")

        safe_filename = os.path.basename(filename)

        candidate_dirs = []

        configured_upload = current_app.config.get("UPLOAD_FOLDER")
        if configured_upload:
            candidate_dirs.append(configured_upload)

        candidate_dirs.extend(
            [
                os.path.join(current_app.root_path, "static", "uploads"),
                os.path.join(os.getcwd(), "app", "static", "uploads"),
                os.path.join(os.getcwd(), "static", "uploads"),
            ]
        )

        checked_paths = []

        for folder in candidate_dirs:
            local_path = os.path.abspath(os.path.join(folder, safe_filename))
            checked_paths.append(local_path)

            current_app.logger.info(
                f"[S3-PROXY] Comprobando fallback local físico: {local_path}"
            )

            if os.path.exists(local_path):
                mime_type, _ = mimetypes.guess_type(local_path)
                mime_type = mime_type or "application/octet-stream"

                current_app.logger.info(
                    f"[S3-PROXY] Archivo local encontrado: {local_path} ({mim_type})"
                )

                return send_file(
                    local_path,
                    mimetype=mime_type,
                    as_attachment=False,
                    download_name=safe_filename,
                    conditional=True,
                )

        current_app.logger.error(
            f"[S3-PROXY] Archivo no encontrado ni en S3 ni localmente. "
            f"Rutas comprobadas: {checked_paths}"
        )

        return {
            "error": "Archivo no encontrado en S3 ni localmente",
            "filename": safe_filename,
            "checked_paths": checked_paths,
        }, 404

    except Exception as e:
        current_app.logger.error(
            f"Error inesperado sirviendo archivo S3 {filename}: {e}"
        )
        return jsonify({"error": "Error interno del servidor"}), 500
