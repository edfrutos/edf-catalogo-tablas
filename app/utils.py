# Script: utils.py
# Descripción: ["Acceso restringido a administradores", "danger"]
# Uso: python3 utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from functools import wraps

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from flask import flash, redirect, session, url_for

from app.extensions import s3_client

ALLOWED_EXTENSIONS = {"xlsx"}


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Acceso restringido a administradores", "danger")
            return redirect(url_for("main.dashboard_user"))
        return f(*args, **kwargs)

    return decorated_function


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def leer_datos_excel(filepath):
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas no está disponible. Instálelo para usar funciones de Excel.")
    df = pd.read_excel(filepath)
    return df.to_dict(orient="records")


def escribir_datos_excel(filepath, data):
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas no está disponible. Instálelo para usar funciones de Excel.")
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)


def eliminar_archivo_imagen(bucket_name, filename):
    if s3_client:
        s3_client.delete_object(Bucket=bucket_name, Key=filename)


def upload_file_to_s3(file, bucket_name, object_name):
    if s3_client:
        s3_client.upload_fileobj(file, bucket_name, object_name)
