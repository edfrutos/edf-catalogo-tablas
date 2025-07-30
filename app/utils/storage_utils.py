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

# Importaciones para Google Drive
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../tools/db_utils'))
    from google_drive_utils import get_drive
except ImportError:
    get_drive = None

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

def get_storage_client():
    """Obtiene un cliente de almacenamiento de Google Drive."""
    try:
        if get_drive is None:
            print("Google Drive utils no disponible")
            return None
        
        # Intentar obtener el cliente de Google Drive
        drive_client = get_drive()
        if drive_client:
            print("Cliente de Google Drive inicializado correctamente")
            return drive_client
        else:
            print("No se pudo inicializar el cliente de Google Drive")
            return None
    except Exception as e:
        print(f"Error al obtener cliente de Google Drive: {e}")
        return None

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
