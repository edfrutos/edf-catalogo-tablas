# app/models.py

import os
import re
import logging
from bson.objectid import ObjectId

# Configurar logging
logger = logging.getLogger(__name__)

# Importar funciones de base de datos desde el módulo database.py
from app.database import (
    get_mongo_client,
    get_mongo_db,
    get_collection,
    get_users_collection as db_get_users_collection,
    get_reset_tokens_collection,
    get_audit_logs_collection,
    get_catalogs_collection as db_get_catalogs_collection,
)

# === Colecciones ===


def get_users_collection():
    """Obtiene la colección de usuarios principal, verificando múltiples colecciones"""
    # Utilizar la función del módulo database.py que ya ha sido implementada
    return db_get_users_collection()


def get_users_unified_collection():
    try:
        return get_collection("users_unified")
    except Exception as e:
        logger.error(f"Error obteniendo colección users_unified: {str(e)}")
        raise


def get_resets_collection():
    try:
        return get_reset_tokens_collection()
    except Exception as e:
        logger.error(f"Error obteniendo colección resets: {str(e)}")
        raise


def get_catalogs_collection():
    try:
        return get_mongo_db()["spreadsheets"]  # type: ignore
    except Exception as e:
        logger.error(f"Error obteniendo colección catalogs: {str(e)}")
        raise


def get_tables_collection():
    try:
        return get_collection("tables")
    except Exception as e:
        logger.error(f"Error obteniendo colección tables: {str(e)}")
        raise


# === Funciones de usuario ===


def find_user_by_email_or_name(identifier):
    """Busca un usuario por email, nombre de usuario o nombre real (insensible a mayúsculas y espacios)"""
    logger.info(f"[find_user_by_email_or_name] INICIO - Buscando: '{identifier}'")
    
    if not identifier:
        logger.warning("[find_user_by_email_or_name] Identificador vacío")
        return None

    # Normalizar el identificador
    identifier = identifier.lower().strip()
    logger.info(f"[find_user_by_email_or_name] Identificador normalizado: '{identifier}'")
    
    collection = get_users_collection()
    logger.info(f"[find_user_by_email_or_name] Colección obtenida: {collection}")

    if collection is None:
        logger.error("No se pudo obtener la colección de usuarios")
        return None

    # 1. Búsqueda exacta insensible a mayúsculas y espacios para username/email/nombre
    # Usamos regex exacto con ^ $ y opción 'i' (sin re.escape)
    query = {
        "$or": [
            {"email": {"$regex": f"^{identifier}$", "$options": "i"}},
            {"username": {"$regex": f"^{identifier}$", "$options": "i"}},
            {"nombre": {"$regex": f"^{identifier}$", "$options": "i"}},
        ]
    }
    logger.info(f"[find_user_by_email_or_name] Query exacta: {query}")
    
    user = collection.find_one(query)
    logger.info(f"[find_user_by_email_or_name] Resultado query exacta: {user is not None}")
    
    if user:
        # Log which field matched
        match_field = None
        for field in ["email", "username", "nombre"]:
            value = user.get(field, "")
            if isinstance(value, str) and value.lower().strip() == identifier:
                match_field = field
                break
        logger.info(
            f"[find_user_by_email_or_name] Usuario encontrado por {match_field if match_field else 'algún campo'}: {user.get('email', user.get('username', user.get('nombre', '')))}"
        )
        return user

    # 2. Búsqueda parcial si el input es suficientemente largo
    if len(identifier) > 3:
        query_partial = {
            "$or": [
                {"email": {"$regex": identifier, "$options": "i"}},
                {"username": {"$regex": identifier, "$options": "i"}},
                {"nombre": {"$regex": identifier, "$options": "i"}},
            ]
        }
        logger.info(f"[find_user_by_email_or_name] Query parcial: {query_partial}")
        
        user = collection.find_one(query_partial)
        logger.info(f"[find_user_by_email_or_name] Resultado query parcial: {user is not None}")
        
        if user:
            logger.info(
                f"[find_user_by_email_or_name] Usuario encontrado por búsqueda parcial: {user.get('email', user.get('username', user.get('nombre', '')))}"
            )
            return user

    # 3. Si no tiene @, probar dominios comunes
    if "@" not in identifier:
        logger.info("[find_user_by_email_or_name] Probando dominios comunes")
        common_domains = [
            "@gmail.com",
            "@hotmail.com",
            "@yahoo.com",
            "@outlook.com",
            "@dominio.com",
        ]
        for domain in common_domains:
            email = f"{identifier}{domain}"
            query_domain = {"email": {"$regex": f"^{email}$", "$options": "i"}}
            logger.info(f"[find_user_by_email_or_name] Probando dominio {domain}: {query_domain}")
            
            user = collection.find_one(query_domain)
            if user:
                logger.info(
                    f"[find_user_by_email_or_name] Usuario encontrado con dominio {domain}: {user.get('email')}"
                )
                return user

    logger.warning(f"[find_user_by_email_or_name] Usuario no encontrado con identificador: {identifier}")
    return None


def find_reset_token(token):
    return get_resets_collection().find_one({"token": token})  # type: ignore


def update_user_password(user_id, new_hashed_password):
    return get_users_collection().update_one(  # type: ignore
        {"_id": ObjectId(user_id)}, {"$set": {"password": new_hashed_password}}
    )


def mark_token_as_used(token_id):
    return get_resets_collection().update_one(  # type: ignore
        {"_id": ObjectId(token_id)}, {"$set": {"used": True}}
    )


# Añadir esta función para verificar si un usuario es admin
def is_admin(user):
    return user.get("role") == "admin"


# Añadir esta para obtener un usuario por ID
def get_user_by_id(user_id):
    return get_users_collection().find_one({"_id": user_id})  # type: ignore


def get_db():
    """Obtiene la conexión a la base de datos principal"""
    # Usamos la función del módulo database.py para mayor consistencia
    return get_mongo_db()
