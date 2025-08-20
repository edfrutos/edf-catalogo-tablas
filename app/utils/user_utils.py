# Script: user_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 user_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import logging
from typing import Any, Dict, List, Optional

from bson.objectid import ObjectId
from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

from app.utils.db_utils import get_db

logger = logging.getLogger(__name__)


def get_user_collection():
    """
    Obtiene la colección de usuarios desde la aplicación actual

    Returns:
        Collection: Colección de MongoDB para usuarios o None si no se puede obtener
    """
    try:
        # Intentar obtener la colección desde flask.g
        if hasattr(g, "users_collection"):
            return g.users_collection
        # Si no está disponible directamente, intentar obtenerla desde la base de datos
        if hasattr(g, "db"):
            return g.db["users"]
        # Si tampoco está disponible, intentar obtenerla desde la extensión mongo
        if hasattr(current_app, "mongo"):
            return current_app.mongo.db.users  # type: ignore
        logger.error("No se pudo encontrar la colección de usuarios")
        return None
    except Exception as e:
        logger.error(f"Error al obtener la colección de usuarios: {str(e)}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su ID

    Args:
        user_id (str): ID del usuario a buscar

    Returns:
        Dict: Documento del usuario o None si no se encuentra
    """
    try:
        collection = get_user_collection()
        if not collection:
            return None

        return collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        logger.error(f"Error al obtener usuario por ID: {str(e)}")
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su nombre de usuario

    Args:
        username (str): Nombre de usuario a buscar

    Returns:
        Dict: Documento del usuario o None si no se encuentra
    """
    try:
        collection = get_user_collection()
        if not collection:
            return None

        return collection.find_one({"username": username})
    except Exception as e:
        logger.error(f"Error al obtener usuario por nombre de usuario: {str(e)}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su correo electrónico

    Args:
        email (str): Correo electrónico a buscar

    Returns:
        Dict: Documento del usuario o None si no se encuentra
    """
    try:
        collection = get_user_collection()
        if not collection:
            return None

        return collection.find_one({"email": email})
    except Exception as e:
        logger.error(f"Error al obtener usuario por email: {str(e)}")
        return None


def create_user(
    username: str, email: str, password: str, role: str = "user"
) -> Optional[str]:
    """
    Crea un nuevo usuario en la base de datos

    Args:
        username (str): Nombre de usuario
        email (str): Correo electrónico
        password (str): Contraseña (se hará hash antes de guardarla)
        role (str): Rol del usuario (por defecto 'user')

    Returns:
        str: ID del usuario creado o None si hay error
    """
    try:
        collection = get_user_collection()
        if not collection:
            return None

        # Verificar si ya existe un usuario con ese nombre o email
        if collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            logger.warning(
                f"Ya existe un usuario con el nombre {username} o email {email}"
            )
            return None

        # Crear el documento del usuario
        user_doc = {
            "username": username,
            "email": email,
            "password": generate_password_hash(password),
            "role": role,
            "active": True,
        }

        result = collection.insert_one(user_doc)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error al crear usuario: {str(e)}")
        return None


def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Actualiza un usuario existente

    Args:
        user_id (str): ID del usuario a actualizar
        update_data (Dict): Datos a actualizar

    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        collection = get_user_collection()
        if not collection:
            return False

        # Si se está actualizando la contraseña, hacer hash
        if "password" in update_data:
            update_data["password"] = generate_password_hash(update_data["password"])

        result = collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )

        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {str(e)}")
        return False


def verify_password(user: Dict[str, Any], password: str) -> bool:
    """
    Verifica si la contraseña proporcionada coincide con la del usuario

    Args:
        user (Dict): Documento del usuario
        password (str): Contraseña a verificar

    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    try:
        if not user or "password" not in user:
            return False

        return check_password_hash(user["password"], password)
    except Exception as e:
        logger.error(f"Error al verificar contraseña: {str(e)}")
        return False


def get_all_users() -> List[Dict[str, Any]]:
    """
    Obtiene todos los usuarios de la base de datos

    Returns:
        List[Dict]: Lista de documentos de usuarios
    """
    try:
        collection = get_user_collection()
        if not collection:
            return []

        return list(collection.find())
    except Exception as e:
        logger.error(f"Error al obtener todos los usuarios: {str(e)}")
        return []


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """
    Cambia la contraseña de un usuario verificando primero la contraseña actual

    Args:
        user_id (str): ID del usuario
        current_password (str): Contraseña actual
        new_password (str): Nueva contraseña

    Returns:
        bool: True si se cambió correctamente, False en caso contrario
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            logger.warning(f"No se encontró el usuario con ID {user_id}")
            return False

        # Verificar la contraseña actual
        if not verify_password(user, current_password):
            logger.warning(
                f"Contraseña actual incorrecta para el usuario {user.get('username')}"
            )
            return False

        # Actualizar la contraseña
        return update_user(user_id, {"password": new_password})
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {str(e)}")
        return False
