# Script: storage_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 storage_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from flask import current_app
import secrets

# Definiciones de carpetas locales
SPREADSHEET_FOLDER = os.path.join(os.getcwd(), "spreadsheets")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "imagenes_subidas")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Inicializar S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def eliminar_archivo_imagen(ruta_imagen):
    """Eliminar un archivo local o de S3"""
    if not ruta_imagen:
        return False

    if ruta_imagen.startswith('s3://'):
        parts = ruta_imagen[5:].split('/', 1)
        if len(parts) == 2:
            bucket_name, object_key = parts
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=object_key)
                return True
            except ClientError as e:
                print(f"Error al eliminar de S3: {e}")
                return False
    else:
        ruta_local = os.path.join(current_app.root_path, ruta_imagen.lstrip('/'))
        if os.path.exists(ruta_local):
            os.remove(ruta_local)
            return True
    return False

def upload_file_to_s3(filepath, object_name=None):
    """Subir un archivo a S3"""
    if not object_name:
        object_name = os.path.basename(filepath)

    try:
        s3_client.upload_file(filepath, os.getenv("S3_BUCKET_NAME"), object_name)
        return True
    except ClientError as e:
        print(f"Error al subir a S3: {e}")
        return False
