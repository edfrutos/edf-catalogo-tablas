# app/models.py

import os
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
    get_catalogs_collection as db_get_catalogs_collection
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
        return get_mongo_db()['spreadsheets']
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
    """Busca un usuario por email o nombre de usuario en múltiples colecciones"""
    print(f"[DEBUG] Buscando usuario: {identifier}")
    if not identifier:
        print("[DEBUG] Identificador vacío")
        return None
        
    identifier = identifier.lower()
    collection = get_users_collection()
    print(f"[DEBUG] Colección de usuarios: {collection}")
    if collection is None:
        logger.error("No se pudo obtener la colección de usuarios")
        print("[DEBUG] No se pudo obtener la colección de usuarios")
        return None
        
    fields = ["email", "username", "nombre"]
    for field in fields:
        user = collection.find_one({field: {"$regex": f"^{identifier}$", "$options": "i"}})
        print(f"[DEBUG] Buscando por {field}: {user}")
        if user:
            logger.info(f"Usuario encontrado por campo {field}")
            print(f"[DEBUG] Usuario encontrado por campo {field}: {user}")
            return user
    user = collection.find_one({
        "$or": [
            {"email": {"$regex": identifier, "$options": "i"}},
            {"username": {"$regex": identifier, "$options": "i"}},
            {"nombre": {"$regex": identifier, "$options": "i"}}
        ]
    })
    print(f"[DEBUG] Búsqueda flexible: {user}")
    if user:
        logger.info("Usuario encontrado con búsqueda flexible")
        print(f"[DEBUG] Usuario encontrado con búsqueda flexible: {user}")
        return user
    print("[DEBUG] Usuario no encontrado")
    return None
def find_reset_token(token):
    return get_resets_collection().find_one({"token": token})

def update_user_password(user_id, new_hashed_password):
    return get_users_collection().update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed_password}}
    )

def mark_token_as_used(token_id):
    return get_resets_collection().update_one(
        {"_id": ObjectId(token_id)},
        {"$set": {"used": True}}
    )

# Añadir esta función para verificar si un usuario es admin
def is_admin(user):
    return user.get("role") == "admin"

# Añadir esta para obtener un usuario por ID
def get_user_by_id(user_id):
    return get_users_collection().find_one({"_id": user_id})

def get_db():
    """Obtiene la conexión a la base de datos principal"""
    # Usamos la función del módulo database.py para mayor consistencia
    return get_mongo_db()
