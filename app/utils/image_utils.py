"""
Utilidades unificadas para manejo de imágenes
"""

import os
from typing import Any, Dict, List

from flask import current_app


def get_unified_image_urls(row_data: Dict[str, Any]) -> List[str]:
    """
    Función unificada para obtener todas las URLs de imágenes de una fila.

    Busca en todos los campos posibles: images, imagenes, imagen_data, Imagen
    Implementa fallback: S3 → Local → Error image

    Args:
        row_data: Diccionario con los datos de la fila

    Returns:
        Lista de URLs válidas para mostrar las imágenes
    """
    image_urls = []

    # Recopilar todas las imágenes de todos los campos
    all_images = []

    # 1. Campo 'images' (principal)
    images = row_data.get("images")
    if isinstance(images, list):
        all_images.extend(images)
    elif isinstance(images, str) and images and images != "N/A":
        all_images.append(images)

    # 2. Campo 'imagenes' (secundario)
    imagenes = row_data.get("imagenes")
    if isinstance(imagenes, list):
        all_images.extend(imagenes)
    elif isinstance(imagenes, str) and imagenes and imagenes != "N/A":
        all_images.append(imagenes)

    # 3. Campo 'imagen_data' (terciario)
    imagen_data = row_data.get("imagen_data")
    if isinstance(imagen_data, list):
        all_images.extend(imagen_data)
    elif isinstance(imagen_data, str) and imagen_data and imagen_data != "N/A":
        all_images.append(imagen_data)

    # 4. Campo 'Imagen' (URL externa)
    imagen_url = row_data.get("Imagen")
    if isinstance(imagen_url, str) and imagen_url and imagen_url.startswith("http"):
        all_images.append(imagen_url)

    # Eliminar duplicados manteniendo orden
    unique_images = list(dict.fromkeys(all_images))

    # Procesar cada imagen con fallback
    for img in unique_images:
        if not img or img == "N/A":
            continue

        if isinstance(img, str) and img.startswith("http"):
            # URL externa - usar directamente
            image_urls.append(img)
        else:
            # Archivo local - implementar fallback S3 → Local → Error
            processed_url = get_image_fallback_url(img)
            image_urls.append(processed_url)

    return image_urls


def get_image_fallback_url(filename: str) -> str:
    """
    Implementa fallback para archivos de imagen: S3 → Local → Error

    Args:
        filename: Nombre del archivo de imagen

    Returns:
        URL válida para mostrar la imagen
    """
    if not filename or filename == "N/A":
        return "/static/img/image-error.svg"

    # 1. Usar proxy S3 para evitar problemas CORS
    s3_proxy_url = f"/admin/s3/{filename}"

    # 2. Fallback local
    local_url = f"/static/uploads/{filename}"

    # 3. Error image
    error_url = "/static/img/image-error.svg"

    # Verificar si existe localmente (para decidir el fallback)
    try:
        local_path = os.path.join(current_app.root_path, "static", "uploads", filename)
        if os.path.exists(local_path):
            current_app.logger.debug(f"[IMAGE] Archivo local encontrado: {filename}")
            return local_url
        else:
            current_app.logger.debug(
                f"[IMAGE] Archivo local no encontrado, usando proxy S3: {filename}"
            )
            return s3_proxy_url
    except Exception as e:
        current_app.logger.error(
            f"[IMAGE] Error verificando archivo local {filename}: {e}"
        )
        return s3_proxy_url


def get_images_for_template(row_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepara los datos de imagen para usar en templates.

    Args:
        row_data: Datos de la fila

    Returns:
        Diccionario con URLs y metadatos de imágenes
    """
    image_urls = get_unified_image_urls(row_data)

    return {
        "imagen_urls": image_urls,
        "num_imagenes": len(image_urls),
        "tiene_imagenes": len(image_urls) > 0,
    }


def get_raw_images_for_edit(row_data: Dict[str, Any]) -> List[str]:
    """
    Obtiene lista de nombres de archivos de imagen para formulario de edición.
    No incluye URLs externas, solo archivos locales/S3.

    Args:
        row_data: Datos de la fila

    Returns:
        Lista de nombres de archivos de imagen
    """
    raw_images = []

    # Recopilar solo archivos (no URLs externas)
    for field in ["images", "imagenes", "imagen_data"]:
        value = row_data.get(field)

        if isinstance(value, list):
            for img in value:
                if (
                    img
                    and img != "N/A"
                    and isinstance(img, str)
                    and not img.startswith("http")
                ):
                    raw_images.append(img)
        elif (
            isinstance(value, str)
            and value
            and value != "N/A"
            and not value.startswith("http")
        ):
            raw_images.append(value)

    # Eliminar duplicados manteniendo orden
    return list(dict.fromkeys(raw_images))


def upload_image_to_s3(file_obj, filename):
    """
    Sube una imagen a S3 usando un objeto de archivo.

    Args:
        file_obj: Objeto de archivo (FileStorage de Flask)
        filename: Nombre del archivo a usar en S3

    Returns:
        str: URL de S3 si tiene éxito, None si falla
    """
    try:
        import os
        import tempfile

        from app.utils.s3_utils import upload_file_to_s3

        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{filename}"
        ) as temp_file:
            # Guardar el contenido del archivo subido al archivo temporal
            file_obj.save(temp_file.name)

            # Subir a S3
            result = upload_file_to_s3(temp_file.name, filename)

            # Limpiar el archivo temporal
            os.unlink(temp_file.name)

            if result.get("success"):
                return result.get("url")
            else:
                current_app.logger.error(f"Error subiendo a S3: {result.get('error')}")
                return None

    except Exception as e:
        current_app.logger.error(f"Error en upload_image_to_s3: {str(e)}")
        return None
