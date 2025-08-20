#!/usr/bin/env python3
# Script: check_users.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 check_users.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

import logging
import os
import sys

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno primero
load_dotenv()

# Añadir el directorio padre al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_collections():
    """Obtener las colecciones de usuarios de forma segura"""
    try:
        from app.models import get_mongo_client, get_mongo_db, get_users_collection

        # Obtener cliente y base de datos
        client = get_mongo_client()
        db = get_mongo_db()

        # Obtener colección principal de usuarios
        users = get_users_collection()

        # Verificar si existe la colección users_unified
        collection_names = db.list_collection_names()
        if 'users_unified' in collection_names:
            unified = db.users_unified
        else:
            logger.warning("La colección 'users_unified' no existe en la base de datos")
            unified = None

        return users, unified, client
    except ImportError as e:
        logger.error(f"Error al importar módulos: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {str(e)}")
        raise

def check_users():
    """Verificar usuarios en ambas colecciones"""
    try:
        users, unified, client = get_collections()

        print("\n=== Usuarios en la colección 'users' ===")
        users_count = 0
        try:
            for user in users.find({}):
                users_count += 1
                print(f"\nID: {user.get('_id')}")
                print(f"Email: {user.get('email')}")
                print(f"Nombre: {user.get('nombre')}")
                print(f"Role: {user.get('role')}")
                # Verificar si existe password antes de mostrar
                if user.get('password'):
                    print(f"Password: {user.get('password')[:20]}...")
                else:
                    print("Password: No definida")
                print(f"Last Login: {user.get('last_login')}")
                print(f"Failed Attempts: {user.get('failed_attempts', 0)}")
                print(f"Locked Until: {user.get('locked_until')}")
        except Exception as e:
            logger.error(f"Error al leer la colección 'users': {str(e)}")

        print(f"\nTotal usuarios en 'users': {users_count}")

        if unified is not None:
            print("\n=== Usuarios en la colección 'users_unified' ===")
            unified_count = 0
            try:
                for user in unified.find({}):
                    unified_count += 1
                    print(f"\nID: {user.get('_id')}")
                    print(f"Email: {user.get('email')}")
                    print(f"Nombre: {user.get('nombre')}")
                    print(f"Role: {user.get('role')}")
                    # Verificar si existe password antes de mostrar
                    if user.get('password'):
                        print(f"Password: {user.get('password')[:20]}...")
                    else:
                        print("Password: No definida")
                    print(f"Last Login: {user.get('last_login')}")
                    print(f"Failed Attempts: {user.get('failed_attempts', 0)}")
                    print(f"Locked Until: {user.get('locked_until')}")
            except Exception as e:
                logger.error(f"Error al leer la colección 'users_unified': {str(e)}")

            print(f"\nTotal usuarios en 'users_unified': {unified_count}")
        else:
            print("\n=== La colección 'users_unified' no existe ===")

        # No cerramos la conexión aquí ya que es gestionada globalmente

    except Exception as e:
        logger.error(f"Error al verificar usuarios: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        logger.info("Iniciando verificación de usuarios...")
        check_users()
        logger.info("Verificación completada exitosamente")
    except Exception as e:
        logger.error(f"Error al verificar usuarios: {str(e)}")
        sys.exit(1)
