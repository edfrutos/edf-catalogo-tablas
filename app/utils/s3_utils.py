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

        # Generar la URL del archivo
        region = os.environ.get("AWS_REGION", "eu-central-1")
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"

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
        bool: True si se eliminó correctamente, False en caso contrario
    """
    # Si no se especifica un bucket, usar el valor de S3_BUCKET_NAME
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        if not bucket_name:
            logger.error(
                "No se especificó un bucket y no se encontró S3_BUCKET_NAME en las variables de entorno"
            )
            return False

    # Obtener el cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        logger.error("No se pudo crear el cliente S3")
        return False

    try:
        # Eliminar el archivo de S3
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        logger.error(f"Error al eliminar archivo de S3: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al eliminar archivo de S3: {str(e)}")
        return False


def get_s3_url(object_name, bucket_name=None):
    """
    Obtiene la URL de un objeto en S3, verificando que existe

    Args:
        object_name (str): Nombre del objeto en S3
        bucket_name (str): Nombre del bucket de S3 (si es None, se usa el valor de S3_BUCKET_NAME)

    Returns:
        str: URL del objeto en S3 si existe, None si no existe
    """
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

    try:
        # Verificar si el objeto existe en S3
        s3_client.head_object(Bucket=bucket_name, Key=object_name)

        # Si llegamos aquí, el objeto existe
        region = os.environ.get("AWS_REGION", "eu-central-1")
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            logger.warning(f"Archivo {object_name} no encontrado en S3")
            return None
        else:
            logger.error(f"Error verificando archivo en S3: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error inesperado verificando archivo en S3: {str(e)}")
        return None
