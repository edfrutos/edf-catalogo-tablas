# Script: s3_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 s3_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import logging
import os

import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Obtiene un cliente de AWS S3 configurado con las credenciales del archivo .env
    """
    try:
        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        aws_region = os.environ.get("AWS_REGION", "eu-central-1")

        if not aws_access_key or not aws_secret_key:
            logger.error(
                "No se encontraron las credenciales de AWS en las variables de entorno"
            )
            return None

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
        )
        return s3_client
    except Exception as e:
        logger.error(f"Error al crear el cliente S3: {str(e)}")
        return None


def upload_file_to_s3_direct(file_obj, object_name, bucket_name=None):
    """
    Sube un archivo directamente a AWS S3 desde un objeto file sin guardar localmente

    Args:
        file_obj: Objeto file de Flask/Werkzeug
        object_name (str): Nombre del objeto en S3
        bucket_name (str): Nombre del bucket de S3 (si es None, se usa el valor de S3_BUCKET_NAME)

    Returns:
        dict: Información del archivo subido (success, url, key) o error
    """
    # Si no se especifica un bucket, usar el valor de S3_BUCKET_NAME
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            return {
                "success": False,
                "error": "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno",
            }

    # Obtener el cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        return {"success": False, "error": "No se pudo crear el cliente S3"}

    try:
        # Reset file pointer to beginning
        file_obj.seek(0)

        # Subir el archivo directamente a S3
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)

        # Generar la URL del archivo usando el proxy S3 para evitar CORS
        url = f"/admin/s3/{object_name}"

        return {"success": True, "url": url, "key": object_name}
    except ClientError as e:
        logger.error(f"Error al subir archivo a S3: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado al subir archivo a S3: {str(e)}")
        return {"success": False, "error": str(e)}


def upload_file_to_s3(file_path, object_name=None, bucket_name=None):
    """
    Sube un archivo a AWS S3

    Args:
        file_path (str): Ruta local del archivo a subir
        object_name (str): Nombre del objeto en S3 (si es None, se usa el nombre del archivo)
        bucket_name (str): Nombre del bucket de S3 (si es None, se usa el valor de S3_BUCKET_NAME)

    Returns:
        dict: Información del archivo subido (success, url, key) o error
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"El archivo {file_path} no existe"}

    # Si no se especifica un nombre de objeto, usar el nombre del archivo
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Si no se especifica un bucket, usar el valor de S3_BUCKET_NAME
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            return {
                "success": False,
                "error": "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno",
            }

    # Obtener el cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        return {"success": False, "error": "No se pudo crear el cliente S3"}

    try:
        # Subir el archivo a S3
        s3_client.upload_file(file_path, bucket_name, object_name)

        # Generar la URL del archivo usando el proxy S3 para evitar CORS
        url = f"/admin/s3/{object_name}"

        return {"success": True, "url": url, "key": object_name}
    except ClientError as e:
        logger.error(f"Error al subir archivo a S3: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado al subir archivo a S3: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_file_from_s3(object_name, bucket_name=None):
    """
    Elimina un archivo de AWS S3

    Args:
        object_name (str): Nombre del objeto en S3
        bucket_name (str): Nombre del bucket de S3 (si es None, se usa el valor de S3_BUCKET_NAME)

    Returns:
        dict: Información del resultado (success, message) o error
    """
    # Si no se especifica un bucket, usar el valor de S3_BUCKET_NAME
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            logger.error(
                "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno"
            )
            return {
                "success": False,
                "error": "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno",
            }

    # Obtener el cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        logger.error("No se pudo crear el cliente S3")
        return {"success": False, "error": "No se pudo crear el cliente S3"}

    try:
        # Eliminar el archivo de S3
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        logger.info(f"Archivo eliminado de S3: {object_name}")
        return {
            "success": True,
            "message": f"Archivo {object_name} eliminado correctamente",
        }
    except ClientError as e:
        logger.error(f"Error al eliminar archivo de S3: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado al eliminar archivo de S3: {str(e)}")
        return {"success": False, "error": str(e)}


def convert_s3_url_to_proxy(s3_url):
    """
    Convierte una URL directa de S3 a una URL del proxy para evitar CORS

    Args:
        s3_url (str): URL directa de S3

    Returns:
        str: URL del proxy S3 o la URL original si no es de S3
    """
    if not s3_url or not isinstance(s3_url, str):
        return s3_url

    # Verificar si es una URL directa de S3
    if "s3.amazonaws.com" in s3_url or "edf-catalogo-tablas.s3" in s3_url:
        try:
            # Extraer el nombre del archivo de la URL
            filename = s3_url.split("/")[-1]

            # Generar URL del proxy manualmente
            proxy_url = f"/admin/s3/{filename}"
            logger.info(f"[S3-PROXY] Convirtiendo URL S3: {s3_url} -> {proxy_url}")
            return proxy_url
        except Exception as e:
            # Si no se puede generar la URL del proxy, devolver la original
            logger.warning(f"[S3-PROXY] Error generando URL del proxy: {e}")
            return s3_url

    return s3_url


def get_s3_url(object_name, bucket_name=None, retry_count=3, retry_delay=1):
    """
    Obtiene la URL de un objeto en S3, verificando que existe con reintentos

    Args:
        object_name (str): Nombre del objeto en S3
        bucket_name (str): Nombre del bucket de S3 (si es None, se usa el valor de S3_BUCKET_NAME)
        retry_count (int): Número de reintentos en caso de no encontrar el archivo
        retry_delay (int): Segundos de espera entre reintentos

    Returns:
        str: URL del objeto en S3 si existe, None si no existe después de todos los reintentos
    """
    import time

    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            logger.error(
                "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno"
            )
            return None

    # Obtener el cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        logger.error("No se pudo crear el cliente S3")
        return None

    for attempt in range(retry_count):
        try:
            # Verificar si el objeto existe en S3
            s3_client.head_object(Bucket=bucket_name, Key=object_name)

            # Si llegamos aquí, el objeto existe - usar proxy S3 para evitar CORS
            if attempt > 0:
                logger.info(
                    f"Archivo {object_name} encontrado en S3 en el intento {attempt + 1}"
                )
            return f"/admin/s3/{object_name}"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                if attempt < retry_count - 1:
                    logger.info(
                        f"Archivo {object_name} no encontrado en S3, reintentando en {retry_delay}s (intento {attempt + 1}/{retry_count})"
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.warning(
                        f"Archivo {object_name} no encontrado en S3 después de {retry_count} intentos"
                    )
                    return None
            else:
                logger.error(f"Error verificando archivo en S3: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error inesperado verificando archivo en S3: {str(e)}")
            return None

    return None


def check_s3_file_exists_fast(object_name, bucket_name=None):
    """
    Verificación rápida de existencia de archivo en S3 (sin reintentos)

    Args:
        object_name (str): Nombre del objeto en S3
        bucket_name (str): Nombre del bucket de S3

    Returns:
        bool: True si el archivo existe, False si no existe
    """
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            logger.error(
                "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno"
            )
            return False

    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        # Verificación rápida sin reintentos
        s3_client.head_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            return False
        else:
            logger.error(f"Error verificando archivo en S3: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado verificando archivo en S3: {str(e)}")
        return False
