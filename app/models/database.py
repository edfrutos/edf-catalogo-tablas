# Script: database.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 database.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

from pymongo import MongoClient
from bson import ObjectId
from flask import current_app
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

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

def find_user_by_email_or_email(email):
    """Busca un usuario por su email."""
    users = get_users_collection()
    return users.find_one({"$or": [{"email": email}, {"email": email}]})

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
