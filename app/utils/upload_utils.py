import logging
import os
import uuid
from typing import Optional

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.utils.s3_utils import upload_file_to_s3, upload_file_to_s3_direct

logger = logging.getLogger(__name__)


def get_upload_dir() -> str:
    """Obtiene la ruta absoluta del directorio de subidas y la crea si no existe."""
    static_folder = current_app.static_folder or os.path.join(
        current_app.root_path, "static"
    )
    folder = os.path.join(static_folder, "uploads")
    os.makedirs(folder, exist_ok=True)
    return folder


def handle_file_upload(file: Optional[FileStorage]) -> Optional[str]:
    """
    Gestiona la subida de un archivo, guardándolo localmente y/o en S3.

    Args:
        file: Objeto FileStorage de Flask o None.

    Returns:
        El nombre del archivo (que es la clave de S3 si se usa S3) si la subida es exitosa, de lo contrario None.
    """
    if not file or not file.filename:
        return None

    try:
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")

        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
        if use_s3:
            logger.info(f"Intentando subir archivo directamente a S3: {filename}")
            result = upload_file_to_s3_direct(file, filename)

            if result and result.get("success"):
                logger.info(f"Archivo subido a S3 exitosamente: {result.get('key')}")
                return filename
            else:
                error_msg = (
                    result.get("error", "Error desconocido en S3")
                    if result
                    else "Resultado de S3 fue None"
                )
                logger.error(
                    f"Fallo al subir a S3: {error_msg}. Usando modo local como fallback: {filename}"
                )
                # Fallback a modo local
                upload_dir = get_upload_dir()
                local_path = os.path.join(upload_dir, filename)
                file.seek(0)  # Reset file pointer
                file.save(local_path)
                logger.info(f"Archivo guardado localmente como fallback: {local_path}")
                return filename
        else:
            # Modo local
            upload_dir = get_upload_dir()
            local_path = os.path.join(upload_dir, filename)
            file.save(local_path)
            logger.info(f"Archivo guardado localmente: {local_path}")
            return filename
    except Exception as e:
        logger.error(
            f"Error inesperado durante la subida de archivo: {e}", exc_info=True
        )
        return None
