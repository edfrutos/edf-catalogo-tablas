# Script: admin_s3.py
# Descripción: Rutas administrativas para servir archivos S3 mediante proxy.
# Autor: EDF Developer

import mimetypes
import os
from app.utils.paths import writable_uploads

import boto3
from botocore.exceptions import ClientError
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    send_file,
    session,
    send_from_directory,
    stream_with_context,
)

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.utils.row_media import display_name

admin_s3_bp = Blueprint("admin_s3", __name__, url_prefix="/admin")


# Protección del proxy en la app de escritorio. El launcher activa EDF_S3_PROXY_AUTH=1;
# el despliegue web no lo define y mantiene el comportamiento anterior.
S3_LINK_MAX_AGE = 3600  # segundos de validez de un enlace firmado


def _s3_auth_enabled() -> bool:
    return os.getenv("EDF_S3_PROXY_AUTH") == "1"


def _s3_signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.secret_key, salt="s3-proxy")


def _s3_key_is_safe(filename: str) -> bool:
    return bool(filename) and not filename.startswith("/") and ".." not in filename.split("/")


def _s3_request_authorized(filename: str) -> bool:
    """Sesión iniciada, o token firmado válido para ESTE archivo (navegador externo)."""
    if not _s3_auth_enabled():
        return True
    if session.get("user_id"):
        return True
    token = request.args.get("t")
    if not token:
        return False
    try:
        return _s3_signer().loads(token, max_age=S3_LINK_MAX_AGE) == filename
    except (BadSignature, SignatureExpired):
        return False


def signed_s3_url(url: str, secret_key: str) -> str:
    """Añade ?t=<token> a una URL local de /admin/s3/ (la usa el launcher al abrir fuera de la app).

    Cualquier otra URL, o una que ya lleve token, se devuelve igual.
    """
    parsed = urlparse(url)
    prefix = "/admin/s3/"
    if parsed.hostname not in ("127.0.0.1", "localhost") or not parsed.path.startswith(prefix):
        return url
    query = parse_qsl(parsed.query, keep_blank_values=True)
    if any(k == "t" for k, _ in query):
        return url
    key = unquote(parsed.path[len(prefix):])
    if not _s3_key_is_safe(key):
        return url
    token = URLSafeTimedSerializer(secret_key, salt="s3-proxy").dumps(key)
    return urlunparse(parsed._replace(query=urlencode(query + [("t", token)])))


@admin_s3_bp.route("/s3-link/<path:filename>")
def s3_signed_link(filename):
    """Devuelve una URL firmada y temporal para abrir el archivo fuera de la app."""
    if not session.get("user_id"):
        return jsonify({"error": "No autorizado"}), 401
    if not _s3_key_is_safe(filename):
        return jsonify({"error": "Ruta no válida"}), 400
    token = _s3_signer().dumps(filename)
    url = f"{request.host_url.rstrip('/')}/admin/s3/{quote(filename)}?t={token}"
    return jsonify({"url": url})


def _content_disposition(filename: str, download: bool) -> str:
    """Cabecera Content-Disposition con el nombre limpio (sin prefijo uuid).

    Con ``download`` se fuerza la descarga; si no, se muestra en línea.
    Se usa filename* (RFC 5987) para admitir tildes y espacios.
    """
    name = display_name(filename)
    kind = "attachment" if download else "inline"
    ascii_name = name.encode("ascii", "ignore").decode() or "archivo"
    ascii_name = ascii_name.replace('"', "")
    return f"{kind}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


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
            Bucket=current_app.config.get("S3_BUCKET_NAME"),
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
            uploads_dir = writable_uploads(os.path.join(current_app.root_path, "static", "uploads"))

        safe_filename = os.path.basename(filename)
        local_path = os.path.join(uploads_dir, safe_filename)

        current_app.logger.info(
            f"[S3-PROXY] Archivo no encontrado en S3, buscando fallback local físico: {local_path}"
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
    if not _s3_key_is_safe(filename):
        return jsonify({"error": "Ruta no válida"}), 400
    if not _s3_request_authorized(filename):
        return jsonify({"error": "No autorizado"}), 401

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

        # Streaming + Range: el navegador empieza a leer (y a decidir si puede
        # decodificar el vídeo) sin esperar a que el proxy baje el archivo entero.
        get_kwargs = {"Bucket": aws_bucket, "Key": filename}
        range_header = request.headers.get("Range")
        if range_header:
            get_kwargs["Range"] = range_header
        response = s3_client.get_object(**get_kwargs)

        body = response["Body"]
        content_type = response.get("ContentType", "application/octet-stream")

        # Si S3 no guardó un tipo útil, se deduce por la extensión. Con
        # application/octet-stream el navegador descarga el vídeo en lugar de
        # reproducirlo.
        if content_type in ("application/octet-stream", "binary/octet-stream", ""):
            guessed, _ = mimetypes.guess_type(filename)
            if guessed:
                content_type = guessed

        if filename.lower().endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.lower().endswith(".txt"):
            content_type = "text/plain"
        elif filename.lower().endswith(".md"):
            # En línea se sirve como texto para que el visor lo lea siempre;
            # el navegador no intenta descargarlo.
            content_type = "text/plain; charset=utf-8"

        status = 206 if range_header and response.get("ContentRange") else 200
        headers = {
            "Content-Disposition": _content_disposition(
                filename, request.args.get("download") == "1"
            ),
            "Cache-Control": "no-cache",
            "Accept-Ranges": "bytes",
        }
        if response.get("ContentLength") is not None:
            headers["Content-Length"] = str(response["ContentLength"])
        if status == 206:
            headers["Content-Range"] = response["ContentRange"]
        if not _s3_auth_enabled():
            headers["Access-Control-Allow-Origin"] = "*"

        current_app.logger.info(
            f"[S3-PROXY] Sirviendo {filename} - estado {status}, "
            f"Tamaño: {response.get('ContentLength')} bytes, Tipo: {content_type}"
        )

        return Response(
            stream_with_context(body.iter_chunks(65536)),
            status=status,
            content_type=content_type,
            headers=headers,
        )

    except ClientError as e:
        current_app.logger.error(f"Error descargando archivo S3 {filename}: {e}")

        if e.response.get("Error", {}).get("Code") == "InvalidRange":
            return Response(status=416)

        safe_filename = os.path.basename(filename)

        candidate_dirs = []

        configured_upload = current_app.config.get("UPLOAD_FOLDER")
        if configured_upload:
            candidate_dirs.append(configured_upload)

        candidate_dirs.extend(
            [
                writable_uploads(os.path.join(current_app.root_path, "static", "uploads")),
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
                    f"[S3-PROXY] Archivo local encontrado: {local_path} ({mime_type})"
                )

                if safe_filename.lower().endswith(".md"):
                    mime_type = "text/plain"
                want_download = request.args.get("download") == "1"
                return send_file(
                    local_path,
                    mimetype=mime_type,
                    as_attachment=want_download,
                    download_name=display_name(safe_filename),
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
