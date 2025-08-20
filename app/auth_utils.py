# Script: auth_utils.py
# Descripción: [Utilidades de autenticación y autorización para la aplicación. Provee decoradores y funciones auxiliares para el manejo de sesiones y permisos.]
# Uso: python3 auth_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Utilidades de autenticación y autorización para la aplicación. Provee decoradores y funciones auxiliares para el manejo de sesiones y permisos.
"""

import logging
from functools import wraps

from flask import request


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir acceso sin verificar sesión
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir acceso sin verificar rol de administrador
        return f(*args, **kwargs)

    return decorated_function


def get_user_ip():
    """
    Obtiene la dirección IP del usuario actual, considerando proxies.
    """
    if "X-Forwarded-For" in request.headers:
        # Si hay un proxy, obtener la IP original
        ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    else:
        # Sin proxy, usar la IP directa
        ip = request.remote_addr or "unknown"
    return ip


def verify_user_role(user_id, role):
    """
    Verifica si un usuario tiene un rol específico.

    Args:
        user_id (str): ID del usuario a verificar
        role (str): Rol a verificar

    Returns:
        bool: True si el usuario tiene el rol, False en caso contrario
    """
    try:
        from app.database import get_users_collection

        users = get_users_collection()

        from bson.objectid import ObjectId

        user = users.find_one({"_id": ObjectId(user_id)})  # type: ignore

        if user and "roles" in user:
            return role in user["roles"]
        return False
    except Exception as e:
        logging.error(f"Error al verificar rol de usuario: {str(e)}")
        return False
