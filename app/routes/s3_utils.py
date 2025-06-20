# Script: s3_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 s3_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
import boto3
import certifi
from botocore.exceptions import ClientError
from flask import current_app as app

# Configuración de AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Inicializar cliente de S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# -------------------------------
# FUNCIONES PARA AWS S3
# -------------------------------

def upload_file_to_s3(file_path, object_name=None, delete_local=True):
    """Sube un archivo a AWS S3.

    Args:
        file_path (str): Ruta local del archivo.
        object_name (str): Nombre con el que guardar en S3. Por defecto, usa el nombre del archivo.
        delete_local (bool): Si es True, elimina el archivo local tras subirlo.

    Returns:
        str|None: Ruta S3 si sube correctamente, None si falla.
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, object_name)
        url = f"s3://{S3_BUCKET_NAME}/{object_name}"

        if delete_local and os.path.exists(file_path):
            os.remove(file_path)

        return url
    except ClientError as e:
        app.logger.error(f"Error al subir archivo a S3: {e}")
        return None

def delete_file_from_s3(object_name):
    """Elimina un archivo de S3."""
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_name)
        return True
    except ClientError as e:
        app.logger.error(f"Error al eliminar archivo de S3: {e}")
        return False

def get_s3_url(object_name, expiration=3600):
    """Genera una URL prefirmada para un objeto en S3 (acceso temporal).

    Args:
        object_name (str): Nombre del objeto en S3.
        expiration (int): Tiempo de expiración de la URL en segundos (por defecto 1 hora).

    Returns:
        str|None: URL prefirmada o None si falla.
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': object_name},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        app.logger.error(f"Error generando URL prefirmada: {e}")
        return None
