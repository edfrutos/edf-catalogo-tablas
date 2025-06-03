#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Añadir el directorio padre al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db_connection, get_users_collection, get_users_unified_collection

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = get_db_connection(tlsCAFile=certifi.where())
db = client.get_database('app_catalogojoyero_nueva')

# Obtener colecciones
users = get_users_collection()
unified = get_users_unified_collection()

def check_users():
    print("\n=== Usuarios en la colección 'users' ===")
    for user in users.find({}):
        print(f"\nID: {user.get('_id')}")
        print(f"Email: {user.get('email')}")
        print(f"Nombre: {user.get('nombre')}")
        print(f"Role: {user.get('role')}")
        print(f"Password: {user.get('password')[:20]}...")  # Mostrar solo los primeros 20 caracteres
        print(f"Last Login: {user.get('last_login')}")
        print(f"Failed Attempts: {user.get('failed_attempts')}")
        print(f"Locked Until: {user.get('locked_until')}")

    print("\n=== Usuarios en la colección 'users_unified' ===")
    for user in unified.find({}):
        print(f"\nID: {user.get('_id')}")
        print(f"Email: {user.get('email')}")
        print(f"Nombre: {user.get('nombre')}")
        print(f"Role: {user.get('role')}")
        print(f"Password: {user.get('password')[:20]}...")  # Mostrar solo los primeros 20 caracteres
        print(f"Last Login: {user.get('last_login')}")
        print(f"Failed Attempts: {user.get('failed_attempts')}")
        print(f"Locked Until: {user.get('locked_until')}")

if __name__ == '__main__':
    try:
        check_users()
    except Exception as e:
        logger.error(f"Error al verificar usuarios: {str(e)}")
        raise
