# Script: images_routes.py
# Descripción: [Ruta inteligente para servir imágenes con fallback S3 -> Local]
# Uso: python3 images_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

from flask import Blueprint, send_from_directory, redirect, request
from app.utils.s3_utils import get_s3_url
from flask import current_app

# Blueprint para servir imágenes con fallback S3 -> Local

images_bp = Blueprint("uploaded_images", __name__)


@images_bp.route("/imagenes_subidas/<filename>")
def uploaded_images(filename):
    """
    Ruta inteligente para servir imágenes con fallback S3 -> Local
    """
    import os
    from flask import abort

    current_app.logger.info(f"Ruta /imagenes_subidas/ llamada para archivo: {filename}")

    # Verificar si se solicita específicamente S3
    s3_param = request.args.get("s3")

    # Si se solicita S3 específicamente
    if s3_param == "true":
        try:
            url = get_s3_url(filename)
            if url:
                return redirect(url)
            else:
                # Si S3 falla, intentar local como fallback
                current_app.logger.warning(
                    f"S3 falló para {filename}, intentando local"
                )
                local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                if os.path.exists(local_path):
                    return send_from_directory(
                        current_app.config["UPLOAD_FOLDER"], filename
                    )
                else:
                    return "❌ Archivo no encontrado en S3 ni local", 404
        except Exception as e:
            current_app.logger.error(f"Error accediendo a S3 para {filename}: {e}")
            # Fallback a local
            local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            if os.path.exists(local_path):
                return send_from_directory(
                    current_app.config["UPLOAD_FOLDER"], filename
                )
            else:
                return "❌ Error de S3 y archivo no encontrado localmente", 404

    # Comportamiento por defecto: intentar S3 primero, luego local
    try:
        # Intentar S3 primero
        url = get_s3_url(filename)
        if url:
            return redirect(url)
    except Exception as e:
        current_app.logger.warning(f"Error accediendo a S3 para {filename}: {e}")

    # Si S3 falla o no está disponible, intentar local
    local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    current_app.logger.info(f"Buscando archivo local en: {local_path}")
    current_app.logger.info(
        f"UPLOAD_FOLDER configurado como: {current_app.config['UPLOAD_FOLDER']}"
    )
    if os.path.exists(local_path):
        current_app.logger.info(f"Archivo encontrado localmente: {local_path}")
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    else:
        current_app.logger.warning(f"Archivo NO encontrado localmente: {local_path}")

    # Si no se encuentra en ningún lado
    return "❌ Archivo no encontrado", 404
