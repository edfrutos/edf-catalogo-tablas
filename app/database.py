# Script: database.py
# Descripción: [Módulo para gestionar la conexión a la base de datos MongoDB de forma resiliente. Permite modo fallback y reconexión automática.]
# Uso: python3 database.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Módulo para gestionar la conexión a la base de datos MongoDB de forma resiliente.
Permite modo fallback y reconexión automática.
"""

import logging
import os
import threading
import time

import certifi  # Añadir al inicio junto con los otros imports
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

# Importar sistemas de caché y fallback
from app.cache_system import cached, get_cache, set_cache
from app.data_fallback import (
    get_fallback_catalogs_by_user,
    get_fallback_user_by_email,
    get_fallback_user_by_id,
    sync_catalogs_to_fallback,
    sync_users_to_fallback,
)
from config import (
    COLLECTION_AUDIT_LOGS,
    COLLECTION_CATALOGOS,
    COLLECTION_RESET_TOKENS,
    COLLECTION_USERS,
    MONGO_CONFIG,
)

# Configuración de logging (solo consola para evitar problemas de permisos)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [DB] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

# Variables globales para acceso a la BD
_mongo_client = None
_mongo_db = None
_is_connected = False
_reconnect_thread = None
_last_error = None


def get_mongo_client():
    """Retorna el cliente MongoDB actual (puede ser None)"""
    global _mongo_client
    return _mongo_client


def get_mongo_db():
    """Retorna la BD MongoDB actual (puede ser None)"""
    global _mongo_db
    return _mongo_db


def is_connected():
    """Indica si hay una conexión activa a MongoDB"""
    global _is_connected
    return _is_connected


def get_last_error():
    """Retorna el último error de conexión"""
    global _last_error
    return _last_error


def initialize_db(app=None):
    """Inicializa la conexión a MongoDB"""
    global _mongo_client, _mongo_db, _is_connected, _last_error

    if app:
        pass

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        if app:
            app.logger.warning("No se ha configurado MONGO_URI")
        logging.warning("No se ha configurado MONGO_URI")
        _last_error = "No se ha configurado MONGO_URI"
        return False

    try:
        # Configuración optimizada para menor consumo de recursos
        config = MONGO_CONFIG.copy()
        config["serverSelectionTimeoutMS"] = 5000  # 5 segundos
        config["maxPoolSize"] = 10  # Limitar el número máximo de conexiones
        config["minPoolSize"] = 1  # Mantener al menos una conexión activa
        config["maxIdleTimeMS"] = (
            30000  # Cerrar conexiones inactivas después de 30 segundos
        )
        config["connectTimeoutMS"] = 5000  # Timeout de conexión reducido
        config["socketTimeoutMS"] = 30000  # Timeout de socket reducido
        config["waitQueueTimeoutMS"] = 5000  # Espera máxima para obtener una conexión
        # Usar siempre tlsCAFile (certifi) si la URI es de tipo mongodb+srv (Atlas SSL)
        if mongo_uri.startswith("mongodb+srv"):
            config["tlsCAFile"] = certifi.where()

        # Fuerza configuración robusta SSL en entorno de tests
        is_testing = os.environ.get("FLASK_ENV") == "testing" or (
            app and getattr(app, "config", {}).get("TESTING", False)
        )
        if is_testing:
            config["tls"] = True
            config["tlsCAFile"] = certifi.where()

        # Intentar establecer la conexión
        _mongo_client = MongoClient(mongo_uri, **config)

        # Verificar que la conexión está activa con un ping
        _mongo_client.admin.command("ping")

        # Si llegamos aquí, la conexión fue exitosa
        _mongo_db = _mongo_client.get_database()
        _is_connected = True
        _last_error = None

        # Sincronizar datos para el fallback
        try:
            try:
                sync_users_to_fallback(_mongo_db[COLLECTION_USERS])

            except Exception as e:
                logging.error(f"Error al sincronizar usuarios para fallback: {str(e)}")
            try:
                sync_catalogs_to_fallback(_mongo_db[COLLECTION_CATALOGOS])

            except Exception as e:
                logging.error(f"Error al sincronizar catálogos para fallback: {str(e)}")
        except Exception as e:
            logging.error(f"Error al sincronizar datos para fallback: {str(e)}")

        return True

    except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
        _last_error = str(e)
        logging.error(f"Error al conectar con MongoDB: {str(e)}")
        if app:
            app.logger.error(f"Error al conectar con MongoDB: {str(e)}")

        _is_connected = False
        return False


def schedule_reconnect(delay=60, app=None):
    """Programa un intento de reconexión después de un tiempo"""
    global _reconnect_thread

    if _reconnect_thread and _reconnect_thread.is_alive():
        return  # Ya hay un intento de reconexión programado

    def reconnect_task():
        logging.info(f"Intentando reconexión a MongoDB después de {delay} segundos...")
        time.sleep(delay)
        initialize_db(app)

    _reconnect_thread = threading.Thread(target=reconnect_task)
    _reconnect_thread.daemon = True
    _reconnect_thread.start()


def get_collection(collection_name, fallback_data=None):
    """
    Obtiene una colección de MongoDB de forma segura.
    Si no hay conexión, retorna None o los datos de fallback.
    """
    global _mongo_db, _is_connected

    # Corregido: los objetos de base de datos en PyMongo no implementan comprobación booleana
    # Por eso debemos comparar explícitamente con None
    if _is_connected is False or _mongo_db is None:
        return fallback_data

    try:
        return _mongo_db[collection_name]
    except Exception as e:
        logging.error(f"Error al acceder a la colección {collection_name}: {str(e)}")
        return fallback_data


# Funciones de utilidad para operaciones comunes


@cached(ttl=3600, key_prefix="user")  # Aumentar TTL a 1 hora para reducir consultas
def get_user_by_email(email):
    """Obtiene un usuario por su email con caché y fallback"""
    # Verificar primero en la caché
    cached_user = get_cache(f"user:{email}")
    if cached_user:
        return cached_user

    # Primero intentamos obtener de MongoDB
    users = get_collection(COLLECTION_USERS)
    if users is not None:
        try:
            # Especificar proyección para traer solo los campos necesarios
            projection = {
                "password": 1,
                "email": 1,
                "role": 1,
                "name": 1,
                "active": 1,
                "_id": 1,
                "last_login": 1,
            }
            user = users.find_one({"email": email}, projection=projection)
            if user:
                # Guardar en caché para futuras consultas
                set_cache(f"user:{email}", user, ttl=3600)
                return user
        except Exception as e:
            logging.error(f"Error al buscar usuario por email: {str(e)}")

    # Si no se encuentra o hay error, usamos el fallback
    fallback_user = get_fallback_user_by_email(email)
    if fallback_user:
        set_cache(f"user:{email}", fallback_user, ttl=3600)
    return fallback_user


@cached(ttl=3600, key_prefix="user")  # Aumentar TTL a 1 hora para reducir consultas
def get_user_by_id(user_id):
    """Obtiene un usuario por su ID con caché y fallback"""
    # Verificar primero en la caché
    cached_user = get_cache(f"user_id:{user_id}")
    if cached_user:
        return cached_user

    # Primero intentamos obtener de MongoDB
    users = get_collection(COLLECTION_USERS)
    if users is not None:
        try:
            from bson.objectid import ObjectId

            # Especificar proyección para traer solo los campos necesarios
            projection = {
                "password": 1,
                "email": 1,
                "role": 1,
                "name": 1,
                "active": 1,
                "_id": 1,
                "last_login": 1,
            }
            user = users.find_one({"_id": ObjectId(user_id)}, projection=projection)
            if user:
                # Guardar en caché para futuras consultas
                set_cache(f"user_id:{user_id}", user, ttl=3600)
                return user
        except Exception as e:
            logging.error(f"Error al buscar usuario por ID: {str(e)}")

    # Si no se encuentra o hay error, usamos el fallback
    fallback_user = get_fallback_user_by_id(user_id)
    if fallback_user:
        set_cache(f"user_id:{user_id}", fallback_user, ttl=3600)
    return fallback_user


@cached(
    ttl=1800, key_prefix="spreadsheets"
)  # Aumentar TTL a 30 minutos para reducir consultas
def get_catalogs_by_user(user_id):
    """Obtiene los catálogos de un usuario con caché y fallback"""
    # Verificar primero en la caché
    cache_key = f"spreadsheets:{user_id}"
    cached_catalogs = get_cache(cache_key)
    if cached_catalogs:
        return cached_catalogs

    # Primero intentamos obtener de MongoDB
    catalogs = get_collection("spreadsheets")
    if catalogs is not None:
        try:
            from bson.objectid import ObjectId

            # Especificar proyección para traer solo los campos necesarios
            projection = {
                "_id": 1,
                "name": 1,
                "description": 1,
                "user_id": 1,
                "created_at": 1,
                "updated_at": 1,
                "status": 1,
            }
            # Agregar límite para evitar traer demasiados documentos
            user_catalogs = list(
                catalogs.find(
                    {"user_id": ObjectId(user_id)}, projection=projection
                ).limit(50)
            )

            if user_catalogs:
                # Guardar en caché para futuras consultas
                set_cache(cache_key, user_catalogs, ttl=1800)
                return user_catalogs
        except Exception as e:
            logging.error(f"Error al buscar catálogos del usuario: {str(e)}")

    # Si no se encuentra o hay error, usamos el fallback
    logging.info(f"Usando fallback para buscar catálogos del usuario: {user_id}")
    fallback_catalogs = get_fallback_catalogs_by_user(user_id)
    if fallback_catalogs:
        set_cache(cache_key, fallback_catalogs, ttl=1800)
    return fallback_catalogs


# Funciones adicionales para acceder a las colecciones


def get_users_collection():
    """Obtiene la colección de usuarios"""
    return get_collection(COLLECTION_USERS)


def get_catalogs_collection():
    """Obtiene la colección de catálogos (unificado a spreadsheets)"""
    return get_collection("spreadsheets")


def get_reset_tokens_collection():
    """Obtiene la colección de tokens de restablecimiento de contraseña"""
    return get_collection(COLLECTION_RESET_TOKENS)


def get_audit_logs_collection():
    """Obtiene la colección de logs de auditoría"""
    return get_collection(COLLECTION_AUDIT_LOGS)
