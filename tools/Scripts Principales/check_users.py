#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Conectar directamente a MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
if not mongo_uri:
    raise ValueError("No se ha configurado MONGO_URI en las variables de entorno")

client: MongoClient = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
db = client[db_name]

# Obtener colecciones
users = db.users
unified = db.users_unified

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
