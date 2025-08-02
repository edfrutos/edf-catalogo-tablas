# Script: data_fallback.py
# Descripción: [Sistema de fallback de datos para cuando la conexión a MongoDB no está disponible. Permite que la aplicación siga funcionando con datos básicos.]
# Uso: python3 data_fallback.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Sistema de fallback de datos para cuando la conexión a MongoDB no está disponible.
Permite que la aplicación siga funcionando con datos básicos.
"""

import os
import json
import logging
from app.cache_system import cached

# Configuración de logging (solo consola para evitar problemas de permisos)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [FALLBACK] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Directorio para almacenar datos de respaldo (cambiado a la carpeta de la app)
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_ROOT, 'app_data')
# Creamos el directorio si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Archivos de datos
USER_DATA_FILE = os.path.join(DATA_DIR, 'edefrutos2025_users_fallback.json')
CATALOG_DATA_FILE = os.path.join(DATA_DIR, 'edefrutos2025_catalogs_fallback.json')

# Datos por defecto
DEFAULT_ADMIN = {
    "email": "admin@example.com",
    "username": "Administrador",
    "password_hash": "$2b$12$B7H/XwI4Qs1UjnZzBZzDk.glBxgdiYpTSYwZrOsNYJUa5WAR3FQuS",  # admin123
    "role": "admin",
    "is_active": True,
    "profile": {"full_name": "Administrador del Sistema"}
}

def ensure_fallback_data():
    """Asegura que existan los archivos de datos básicos"""
    # Datos de usuarios
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump([DEFAULT_ADMIN], f)
            logging.info(f"Creado archivo de respaldo de usuarios: {USER_DATA_FILE}")
    
    # Datos de catálogos
    if not os.path.exists(CATALOG_DATA_FILE):
        with open(CATALOG_DATA_FILE, 'w') as f:
            json.dump([], f)
            logging.info(f"Creado archivo de respaldo de catálogos: {CATALOG_DATA_FILE}")

def save_user_data(users):
    """Guarda datos de usuarios para modo sin conexión"""
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users, f)
        logging.info(f"Datos de usuarios guardados: {len(users)} usuarios")
        return True
    except Exception as e:
        logging.error(f"Error al guardar datos de usuarios: {str(e)}")
        return False

def save_catalog_data(catalogs):
    """Guarda datos de catálogos para modo sin conexión"""
    try:
        with open(CATALOG_DATA_FILE, 'w') as f:
            json.dump(catalogs, f)
        
        return True
    except Exception as e:
        logging.error(f"Error al guardar datos de catálogos: {str(e)}")
        return False

@cached(ttl=300, key_prefix='fallback')
def get_fallback_users():
    """Obtiene usuarios del modo sin conexión"""
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error al leer datos de usuarios: {str(e)}")
        return [DEFAULT_ADMIN]

@cached(ttl=300, key_prefix='fallback')  
def get_fallback_catalogs():
    """Obtiene catálogos del modo sin conexión"""
    try:
        with open(CATALOG_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error al leer datos de catálogos: {str(e)}")
        return []

def get_fallback_user_by_email(email):
    """Busca un usuario por email en el modo sin conexión"""
    users = get_fallback_users()
    for user in users:
        if user.get('email') == email:
            return user
    return None

def get_fallback_user_by_id(user_id):
    """Busca un usuario por ID en el modo sin conexión"""
    users = get_fallback_users()
    for user in users:
        if str(user.get('_id', '')) == str(user_id):
            return user
    return None

def get_fallback_catalogs_by_user(user_id):
    """Obtiene catálogos de un usuario en el modo sin conexión"""
    catalogs = get_fallback_catalogs()
    return [catalog for catalog in catalogs if str(catalog.get('user_id', '')) == str(user_id)]

# Funciones para sincronizar datos
def sync_users_to_fallback(users_collection):
    """Sincroniza usuarios de MongoDB a archivos locales"""
    try:
        users = list(users_collection.find({}, {'password_hash': 1, 'email': 1, 'username': 1, 'role': 1, 'is_active': 1, 'profile': 1}))
        
        # Convertir ObjectId a str para JSON
        for user in users:
            if '_id' in user:
                user['_id'] = str(user['_id'])
        
        return save_user_data(users)
    except Exception as e:
        logging.error(f"Error al sincronizar usuarios: {str(e)}")
        return False

def sync_catalogs_to_fallback(catalogs_collection):
    """Sincroniza catálogos de MongoDB a archivos locales"""
    try:
        catalogs = list(catalogs_collection.find({}, {'name': 1, 'description': 1, 'user_id': 1, 'items': 1, 'is_public': 1}))
        
        # Convertir ObjectId a str para JSON
        for catalog in catalogs:
            if '_id' in catalog:
                catalog['_id'] = str(catalog['_id'])
            if 'user_id' in catalog:
                catalog['user_id'] = str(catalog['user_id'])
        
        return save_catalog_data(catalogs)
    except Exception as e:
        logging.error(f"Error al sincronizar catálogos: {str(e)}")
        return False

# Asegurar que los datos de respaldo existan al cargar el módulo
ensure_fallback_data()
