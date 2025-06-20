# Script: image_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 image_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
import logging
import uuid
from flask import url_for, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def get_image_path(image_filename):
    """
    Obtiene la ruta absoluta de una imagen en el sistema de archivos
    
    Args:
        image_filename (str): Nombre del archivo de imagen
        
    Returns:
        str: Ruta absoluta de la imagen
    """
    try:
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        return os.path.join(upload_folder, image_filename)
    except Exception as e:
        logger.error(f"Error al obtener ruta de imagen: {str(e)}")
        return None

def save_image(uploaded_file, directory='uploads'):
    """
    Guarda una imagen subida por el usuario
    
    Args:
        uploaded_file: Objeto de archivo subido (request.files)
        directory (str): Directorio donde guardar la imagen (relativo a static)
        
    Returns:
        str: Nombre del archivo guardado o None si hay error
    """
    try:
        if not uploaded_file:
            logger.error("No se proporcionó ningún archivo")
            return None
            
        # Generar un nombre de archivo seguro y único
        filename = secure_filename(uploaded_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Asegurar que el directorio existe
        upload_folder = os.path.join(current_app.static_folder, directory)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Guardar el archivo
        file_path = os.path.join(upload_folder, unique_filename)
        uploaded_file.save(file_path)
        
        use_s3 = os.environ.get('USE_S3', 'false').lower() == 'true'
        if use_s3:
            try:
                # Si S3 está habilitado, subir también a S3
                from app.utils.s3_utils import upload_to_s3
                s3_success = upload_to_s3(file_path, unique_filename)
                if not s3_success:
                    logger.warning(f"No se pudo subir la imagen a S3: {unique_filename}")
            except ImportError:
                logger.warning("No se pudo importar s3_utils, la imagen solo se guardará localmente")
        
        return unique_filename
    except Exception as e:
        logger.error(f"Error al guardar imagen: {str(e)}")
        return None

def delete_image(image_filename):
    """
    Elimina una imagen del sistema de archivos y de S3 si está habilitado
    
    Args:
        image_filename (str): Nombre del archivo de imagen a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        if not image_filename:
            return False
            
        # Eliminar del sistema de archivos local
        file_path = get_image_path(image_filename)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar de S3 si está habilitado
        use_s3 = os.environ.get('USE_S3', 'false').lower() == 'true'
        if use_s3:
            try:
                from app.utils.s3_utils import delete_from_s3
                s3_success = delete_from_s3(image_filename)
                if not s3_success:
                    logger.warning(f"No se pudo eliminar la imagen de S3: {image_filename}")
            except ImportError:
                logger.warning("No se pudo importar s3_utils, la imagen solo se eliminará localmente")
        
        return True
    except Exception as e:
        logger.error(f"Error al eliminar imagen: {str(e)}")
        return False

def get_image_url(image_filename):
    """
    Obtiene la URL de una imagen, ya sea desde el servidor local o desde AWS S3
    
    Args:
        image_filename (str): Nombre del archivo de imagen
        
    Returns:
        str: URL de la imagen
    """
    try:
        use_s3 = os.environ.get('USE_S3', 'false').lower() == 'true'
        
        if use_s3:
            # Si está habilitado S3, devolver la URL de S3
            from app.utils.s3_utils import get_s3_url
            s3_url = get_s3_url(image_filename)
            if s3_url:
                return s3_url
        
        # Si no está habilitado S3 o no se pudo obtener la URL de S3, devolver la URL local
        return url_for('static', filename=f'uploads/{image_filename}')
    except Exception as e:
        logger.error(f"Error al obtener URL de imagen: {str(e)}")
        # En caso de error, devolver la URL local
        return url_for('static', filename=f'uploads/{image_filename}')
