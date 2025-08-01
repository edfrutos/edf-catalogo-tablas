#!/usr/bin/env python3
"""
Script para acceso directo a funciones administrativas sin pasar por la interfaz web.
Este script permite:
1. Forzar la creación/actualización del usuario administrador
2. Listar usuarios del sistema
3. Desbloquear cuentas de usuario
4. Verificar la conexión a MongoDB
5. Ejecutar operaciones de mantenimiento
"""

import os
import sys
import logging
import getpass
import time
import uuid
import json
import threading
from datetime import datetime, timedelta
import certifi

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ADMIN_SHELL] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("admin_shell")

# Cargar dependencias necesarias para la aplicación
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError as e:
    logger.error(f"Error al importar dependencias: {str(e)}")
    logger.error("Asegúrate de tener instaladas las dependencias necesarias:")
    logger.error("  pip install pymongo werkzeug")
    sys.exit(1)

# Variables globales
mongo_client = None
mongo_db = None
db_name = "app_catalogojoyero_nueva"  # Nombre por defecto

os.environ['SSL_CERT_FILE'] = certifi.where()

def connect_to_mongodb():
    """Establece conexión con MongoDB"""
    global mongo_client, mongo_db, db_name
    
    try:
        # Intentar obtener la URI de MongoDB desde variables de entorno o archivo de configuración
        mongo_uri = os.environ.get("MONGO_URI", None)
        
        # Si no está definida, usar la URI por defecto
        if not mongo_uri:
            try:
                # Intentar cargar desde config.py
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from config import Config
                mongo_uri = Config.MONGO_URI
                logger.info("URI de MongoDB cargada desde config.py")
            except (ImportError, AttributeError):
                # Usar URI hardcodeada como último recurso
                mongo_uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
                logger.warning("Usando URI de MongoDB hardcodeada por defecto")
        
        # Extraer nombre de base de datos de la URI
        if mongo_uri and "mongodb" in mongo_uri and "/" in mongo_uri:
            uri_parts = mongo_uri.split("/")
            if len(uri_parts) > 3:
                db_name_part = uri_parts[3].split("?")[0]
                if db_name_part:
                    db_name = db_name_part
        
        logger.info(f"Conectando a MongoDB: {mongo_uri[:20]}...")
        
        # Configuración de conexión con mayores tiempos de espera
        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=20000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
            tlsCAFile=certifi.where()
        )
        
        # Verificar conexión con un ping
        mongo_client.admin.command('ping')
        
        # Conectar a la base de datos
        mongo_db = mongo_client[db_name]
        
        logger.info(f"Conexión a MongoDB establecida. Base de datos: {db_name}")
        return True
    except ConnectionFailure as e:
        logger.error(f"Error de conexión a MongoDB: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado en conexión a MongoDB: {str(e)}")
        return False

def get_user_collection():
    """Obtiene la colección de usuarios"""
    global mongo_db
    
    if mongo_db is None:
        logger.error("Base de datos no inicializada")
        return None
    
    # Determinar qué colección usar
    collections = mongo_db.list_collection_names()
    
    if "users" in collections:
        return mongo_db.users
    elif "usuarios" in collections:
        return mongo_db.usuarios
    elif "users_unified" in collections:
        return mongo_db.users_unified
    else:
        logger.error("No se encontró ninguna colección de usuarios")
        return None

def ensure_admin_user():
    """Crea o actualiza el usuario administrador"""
    users_collection = get_user_collection()
    if users_collection is None:
        return False
    
    try:
        # Datos del administrador
        admin_email = "admin@example.com"
        admin_password = "admin123"
        admin_pass_hash = generate_password_hash(admin_password)
        
        # Verificar si el usuario ya existe
        admin_user = users_collection.find_one({"email": admin_email})
        
        if admin_user:
            logger.info(f"Usuario administrador encontrado: {admin_email}")
            
            # Determinar qué username usar - evitar duplicados
            existing_admin = users_collection.find_one({"username": "admin", "email": {"$ne": admin_email}})
            admin_username = "administrator" if existing_admin else "admin"
            
            # Actualizar usuario
            result = users_collection.update_one(
                {"email": admin_email},
                {
                    "$set": {
                        "password": admin_pass_hash,
                        "role": "admin",
                        "active": True,
                        "is_active": True,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "username": admin_username,
                        "nombre": "Administrador"
                    }
                }
            )
            
            logger.info(f"Usuario administrador actualizado: {result.modified_count} documentos")
        else:
            # Crear nuevo usuario administrador
            # Verificar si hay otro usuario con username 'admin'
            existing_admin = users_collection.find_one({"username": "admin"})
            admin_username = "administrator" if existing_admin else "admin"
            
            new_admin = {
                "email": admin_email,
                "password": admin_pass_hash,
                "username": admin_username,
                "nombre": "Administrador",
                "role": "admin",
                "active": True,
                "is_active": True,
                "failed_attempts": 0,
                "locked_until": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = users_collection.insert_one(new_admin)
            logger.info(f"Nuevo usuario administrador creado con ID: {result.inserted_id}")
        
        # Mostrar información actualizada
        updated_admin = users_collection.find_one({"email": admin_email})
        if updated_admin:
            logger.info("Datos del usuario administrador:")
            logger.info(f"  Email: {updated_admin.get('email')}")
            logger.info(f"  Username: {updated_admin.get('username')}")
            logger.info(f"  Role: {updated_admin.get('role')}")
            logger.info(f"  Active: {updated_admin.get('active')} / {updated_admin.get('is_active')}")
            
            # Mostrar credenciales para acceso
            print("\n" + "="*50)
            print(" CREDENCIALES DE ADMINISTRADOR CONFIGURADAS ")
            print("="*50)
            print(f"Email:      {admin_email}")
            print(f"Password:   {admin_password}")
            print(f"Username:   {updated_admin.get('username')}")
            print("="*50 + "\n")
            
            return True
        else:
            logger.error("No se pudo verificar el usuario administrador después de actualizar/crear")
            return False
    except Exception as e:
        logger.error(f"Error al asegurar usuario administrador: {str(e)}")
        return False

def list_users():
    """Lista todos los usuarios del sistema"""
    users_collection = get_user_collection()
    if users_collection is None:
        return False
    
    try:
        # Obtener todos los usuarios
        users = list(users_collection.find({}, {"email": 1, "username": 1, "nombre": 1, "role": 1, "active": 1, "is_active": 1, "locked_until": 1}))
        
        if not users:
            logger.info("No se encontraron usuarios en la base de datos")
            return False
        
        print("\n" + "="*80)
        print(" USUARIOS DEL SISTEMA ".center(80))
        print("="*80)
        print(f"{'EMAIL':<30} {'USERNAME':<20} {'ROLE':<15} {'STATE':<15}")
        print("-"*80)
        
        for user in users:
            email = user.get('email', 'N/A')
            username = user.get('username', 'N/A')
            role = user.get('role', 'user')
            
            # Determinar estado
            is_active = user.get('active', False) or user.get('is_active', False)
            locked_until = user.get('locked_until')
            
            if locked_until and isinstance(locked_until, datetime) and locked_until > datetime.utcnow():
                state = "LOCKED"
            elif is_active:
                state = "ACTIVE"
            else:
                state = "INACTIVE"
            
            print(f"{email:<30} {username:<20} {role:<15} {state:<15}")
        
        print("="*80)
        print(f"Total: {len(users)} usuarios")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Error al listar usuarios: {str(e)}")
        return False

def unlock_user():
    """Desbloquea una cuenta de usuario"""
    users_collection = get_user_collection()
    if users_collection is None:
        return False
    
    try:
        # Solicitar email del usuario a desbloquear
        email = input("Introduce el email del usuario a desbloquear: ").strip().lower()
        
        # Buscar el usuario
        user = users_collection.find_one({"email": email})
        
        if not user:
            logger.error(f"No se encontró ningún usuario con el email: {email}")
            return False
        
        # Actualizar el usuario para desbloquearlo
        result = users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "active": True,
                    "is_active": True,
                    "failed_attempts": 0,
                    "locked_until": None
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Usuario {email} desbloqueado correctamente")
            return True
        else:
            logger.info(f"El usuario {email} ya estaba desbloqueado")
            return True
    except Exception as e:
        logger.error(f"Error al desbloquear usuario: {str(e)}")
        return False

def verify_session_config():
    """Verifica y muestra la configuración de sesiones"""
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Intentar cargar configuración de app/__init__.py
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "__init__.py"), "r") as f:
            init_content = f.read()
        
        print("\n" + "="*80)
        print(" CONFIGURACIÓN DE SESIONES ".center(80))
        print("="*80)
        
        # Buscar configuraciones clave
        session_config_lines = []
        in_session_config = False
        
        for line in init_content.split('\n'):
            if "app.config.update(" in line:
                in_session_config = True
                session_config_lines.append(line)
            elif in_session_config and ")" in line:
                session_config_lines.append(line)
                in_session_config = False
            elif in_session_config:
                session_config_lines.append(line)
        
        if session_config_lines:
            for line in session_config_lines:
                print(line)
        else:
            print("No se encontró configuración de sesiones en app/__init__.py")
        
        # Verificar secret_key
        secret_key_lines = [line for line in init_content.split('\n') if "secret_key" in line.lower()]
        
        if secret_key_lines:
            print("\nCONFIGURACIÓN DE SECRET KEY:")
            for line in secret_key_lines:
                print(line)
        else:
            print("\nNo se encontró configuración de SECRET_KEY en app/__init__.py")
        
        print("="*80 + "\n")
        return True
    except Exception as e:
        logger.error(f"Error al verificar configuración de sesiones: {str(e)}")
        return False

def print_help():
    """Muestra la ayuda del script"""
    print("\n" + "="*80)
    print(" AYUDA DE ADMIN_SHELL.PY ".center(80))
    print("="*80)
    print("Comandos disponibles:")
    print("  1. admin   - Asegura que existe el usuario administrador con la contraseña correcta")
    print("  2. users   - Lista todos los usuarios del sistema")
    print("  3. unlock  - Desbloquea una cuenta de usuario")
    print("  4. session - Verifica la configuración de sesiones")
    print("  5. help    - Muestra esta ayuda")
    print("  6. exit    - Sale del script")
    print("="*80 + "\n")

def main():
    """Función principal del script"""
    logger.info("Iniciando admin_shell.py")
    
    # Conectar a MongoDB
    if not connect_to_mongodb():
        logger.error("No se pudo conectar a MongoDB. Saliendo...")
        return False
    
    # Loop principal
    while True:
        try:
            command = input("\nComando (help para ayuda): ").strip().lower()
            
            if command == "exit":
                logger.info("Saliendo del script")
                break
            elif command == "help":
                print_help()
            elif command == "admin":
                ensure_admin_user()
            elif command == "users":
                list_users()
            elif command == "unlock":
                unlock_user()
            elif command == "session":
                verify_session_config()
            else:
                logger.error(f"Comando no reconocido: {command}")
                print("Usa 'help' para ver los comandos disponibles")
        except KeyboardInterrupt:
            logger.info("\nOperación cancelada por el usuario")
            break
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
    
    # Cerrar conexión a MongoDB
    if mongo_client:
        mongo_client.close()
        logger.info("Conexión a MongoDB cerrada")
    
    return True

if __name__ == "__main__":
    main()
