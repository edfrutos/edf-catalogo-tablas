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


def serve_default_image():
    """Sirve una imagen por defecto cuando no se encuentra el archivo solicitado"""
    import os

    current_app.logger.info("serve_default_image: Función llamada")

    # Primero intentar imagen específica para 'no encontrado'
    default_image_path = os.path.join(
        current_app.config.get("UPLOAD_FOLDER", ""), "default_not_found.png"
    )

    # Si no existe, usar la imagen de perfil por defecto
    if not os.path.exists(default_image_path):
        default_image_path = os.path.join(
            current_app.root_path, "static", "default_profile.png"
        )

    if os.path.exists(default_image_path):
        return send_from_directory(
            os.path.dirname(default_image_path), os.path.basename(default_image_path)
        )

    # Si no hay imagen por defecto disponible, devolver 404
    current_app.logger.error(
        "serve_default_image: No se encontró ninguna imagen por defecto"
    )
    return "❌ Imagen no encontrada", 404


@images_bp.route("/imagenes_subidas/<filename>")
def uploaded_images(filename):
    """
    Ruta inteligente para servir imágenes con fallback S3 -> Local
    """
    import os
    from flask import abort  # noqa: F401

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
                    # Servir imagen por defecto directamente
                    default_path = os.path.join(
                        current_app.root_path, "static", "default_profile.png"
                    )
                    if os.path.exists(default_path):
                        return send_from_directory(
                            os.path.join(current_app.root_path, "static"),
                            "default_profile.png",
                        )
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
                # Servir imagen por defecto directamente
                default_path = os.path.join(
                    current_app.root_path, "static", "default_profile.png"
                )
                if os.path.exists(default_path):
                    return send_from_directory(
                        os.path.join(current_app.root_path, "static"),
                        "default_profile.png",
                    )
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

    # Si no se encuentra en ningún lado, usar imagen por defecto
    current_app.logger.info(f"Usando imagen por defecto para: {filename}")

    # Directamente servir imagen por defecto
    default_image_path = os.path.join(
        current_app.root_path, "static", "default_profile.png"
    )
    current_app.logger.info(f"Sirviendo imagen por defecto desde: {default_image_path}")

    if os.path.exists(default_image_path):
        return send_from_directory(
            os.path.join(current_app.root_path, "static"), "default_profile.png"
        )
    else:
        current_app.logger.error(
            f"Imagen por defecto no encontrada en: {default_image_path}"
        )
        return "❌ Archivo no encontrado", 404
