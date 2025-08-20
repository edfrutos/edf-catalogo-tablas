# Script: database.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 database.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

import logging
import os
from datetime import datetime, timedelta

from bson import ObjectId
from dotenv import load_dotenv
from flask import current_app
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logger = logging.getLogger(__name__)

# Variables globales para la conexión a MongoDB
client = None
db = None
users_collection = None
resets_collection = None

def get_mongo_client():
    """Obtiene el cliente de MongoDB."""
    global client
    if client is None:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        if not mongo_uri:
            raise ValueError("No se ha configurado MONGO_URI en las variables de entorno")
        # Usamos solo tlsAllowInvalidCertificates ya que es el más moderno y recomendado
        client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
        logger.info(f"Conectado a MongoDB: {mongo_uri.split('@')[-1]}")
    return client

def get_mongo_db():
    """
    Obtiene la base de datos de MongoDB.
    """
    global db
    client = get_mongo_client()
    db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
    return client[db_name]

def get_users_collection():
    """Obtiene la colección de usuarios."""
    global users_collection
    if users_collection is None:
        db = get_mongo_db()
        users_collection = db.users
    return users_collection

def get_resets_collection():
    """Obtiene la colección de reseteos de contraseña."""
    global resets_collection
    if resets_collection is None:
        db = get_mongo_db()
        resets_collection = db.password_resets
    return resets_collection

def find_user_by_email_or_email(identifier):
    """Busca un usuario por email, nombre de usuario o nombre real (insensible a mayúsculas y espacios)"""
    logger.info(f"[find_user_by_email_or_email] INICIO - Buscando: '{identifier}'")

    if not identifier:
        logger.warning("[find_user_by_email_or_email] Identificador vacío")
        return None

    # Normalizar el identificador
    identifier = identifier.lower().strip()
    logger.info(f"[find_user_by_email_or_email] Identificador normalizado: '{identifier}'")

    collection = get_users_collection()
    logger.info(f"[find_user_by_email_or_email] Colección obtenida: {collection}")

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
    logger.info(f"[find_user_by_email_or_email] Query exacta: {query}")

    user = collection.find_one(query)
    logger.info(f"[find_user_by_email_or_email] Resultado query exacta: {user is not None}")

    if user:
        # Log which field matched
        match_field = None
        for field in ["email", "username", "nombre"]:
            value = user.get(field, "")
            if isinstance(value, str) and value.lower().strip() == identifier:
                match_field = field
                break
        logger.info(
            f"[find_user_by_email_or_email] Usuario encontrado por {match_field if match_field else 'algún campo'}: {user.get('email', user.get('username', user.get('nombre', '')))}"
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
        logger.info(f"[find_user_by_email_or_email] Query parcial: {query_partial}")

        user = collection.find_one(query_partial)
        logger.info(f"[find_user_by_email_or_email] Resultado query parcial: {user is not None}")

        if user:
            logger.info(
                f"[find_user_by_email_or_email] Usuario encontrado por búsqueda parcial: {user.get('email', user.get('username', user.get('nombre', '')))}"
            )
            return user

    # 3. Si no tiene @, probar dominios comunes
    if "@" not in identifier:
        logger.info("[find_user_by_email_or_email] Probando dominios comunes")
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
            logger.info(f"[find_user_by_email_or_email] Probando dominio {domain}: {query_domain}")

            user = collection.find_one(query_domain)
            if user:
                logger.info(
                    f"[find_user_by_email_or_email] Usuario encontrado con dominio {domain}: {user.get('email')}"
                )
                return user

    logger.warning(f"[find_user_by_email_or_email] Usuario no encontrado con identificador: {identifier}")
    return None

def find_reset_token(token):
    """Busca un token de reseteo de contraseña."""
    resets = get_resets_collection()
    return resets.find_one({"token": token, "used": False, "expires_at": {"$gt": datetime.utcnow()}})

def update_user_password(user_id, new_password):
    """Actualiza la contraseña de un usuario."""
    users = get_users_collection()
    result = users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_password, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0

def mark_token_as_used(token_id):
    """Marca un token como usado."""
    resets = get_resets_collection()
    result = resets.update_one(
        {"_id": ObjectId(token_id)},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )
    return result.modified_count > 0
