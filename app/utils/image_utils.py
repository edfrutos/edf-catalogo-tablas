"""
Utilidades unificadas para manejo de imágenes
"""

import os
from typing import Any, Dict, List, Optional

from flask import current_app


def get_unified_image_urls(row_data: Dict[str, Any]) -> List[str]:
    """
    Función unificada optimizada para obtener todas las URLs de imágenes de una fila.

    Busca en todos los campos posibles: images, imagenes, imagen_data, Imagen
    Implementa fallback optimizado: Local → S3 → None

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

    # Procesar cada imagen con fallback optimizado
    for img in unique_images:
        if not img or img == "N/A":
            continue

        if isinstance(img, str) and (
            img.startswith("http") or img.startswith("/admin/s3/")
        ):
            # URL externa o S3 - usar directamente
            image_urls.append(img)
        else:
            # Archivo local - implementar fallback optimizado Local → S3 → None
            processed_url = get_image_fallback_url(img)
            if processed_url:  # Solo agregar si la URL es válida
                image_urls.append(processed_url)

    return image_urls


def clear_s3_cache(filename: Optional[str] = None):
    """
    Limpia el cache de S3 para un archivo específico o todo el cache

    Args:
        filename: Nombre del archivo específico a limpiar, o None para limpiar todo
    """
    if hasattr(current_app, "s3_cache"):
        if filename:
            cache_key = f"s3_exists_{filename}"
            if cache_key in current_app.s3_cache:
                del current_app.s3_cache[cache_key]
                current_app.logger.debug(f"Cache S3 limpiado para: {filename}")
        else:
            current_app.s3_cache.clear()
            current_app.logger.debug("Cache S3 completamente limpiado")


def get_image_fallback_url(filename: str) -> Optional[str]:
    """
    Implementa fallback optimizado para archivos de imagen: Local → S3 → None

    Args:
        filename: Nombre del archivo de imagen

    Returns:
        URL válida para mostrar la imagen, o None si no existe
    """
    if not filename or filename == "N/A":
        return None  # No devolver URL para archivos vacíos

    # 1. Verificar si existe localmente (más rápido)
    try:
        local_path = os.path.join(current_app.root_path, "static", "uploads", filename)
        if os.path.exists(local_path):
            current_app.logger.debug(f"[IMAGE] Archivo local encontrado: {filename}")
            return f"/static/uploads/{filename}"
    except Exception as e:
        current_app.logger.error(
            f"[IMAGE] Error verificando archivo local {filename}: {e}"
        )

    # 2. Solo verificar S3 si no existe localmente (evitar verificaciones dobles)
    # Usar verificación rápida sin reintentos para evitar lentitud
    try:
        from app.utils.s3_utils import check_s3_file_exists_fast

        if hasattr(current_app, "s3_cache"):
            # Usar cache si está disponible
            cache_key = f"s3_exists_{filename}"
            if cache_key in current_app.s3_cache:
                if current_app.s3_cache[cache_key]:
                    return f"/admin/s3/{filename}"
                else:
                    return None

        # Verificación rápida de S3 (sin reintentos)
        s3_exists = check_s3_file_exists_fast(filename)
        if s3_exists:
            # Cachear resultado positivo
            if not hasattr(current_app, "s3_cache"):
                current_app.s3_cache = {}
            current_app.s3_cache[f"s3_exists_{filename}"] = True
            current_app.logger.debug(f"[IMAGE] Archivo S3 encontrado: {filename}")
            return f"/admin/s3/{filename}"
        else:
            # Cachear resultado negativo
            if not hasattr(current_app, "s3_cache"):
                current_app.s3_cache = {}
            current_app.s3_cache[f"s3_exists_{filename}"] = False

    except Exception as e:
        current_app.logger.error(
            f"[IMAGE] Error verificando archivo S3 {filename}: {e}"
        )

    # 3. Si no existe en ningún lado, no devolver URL
    current_app.logger.debug(f"[IMAGE] Archivo no encontrado: {filename}")
    return None


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
