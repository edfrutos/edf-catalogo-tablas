#!/usr/bin/env python3
"""
Script para reparar el acceso de administrador.
Este script:
1. Conecta directamente a MongoDB
2. Asegura que existe el usuario administrador
3. Resetea la contraseña del administrador a un valor conocido
"""

import logging
import os
import sys
from datetime import datetime

import certifi
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [REPAIR] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("repair_admin")

os.environ['SSL_CERT_FILE'] = certifi.where()

def main():
    # Conectar a MongoDB
    try:
        # Usar la URI de config.py si está disponible
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from config import Config
        mongo_uri = Config.MONGO_URI
        logger.info("URI de MongoDB cargada desde config.py")
    except (ImportError, AttributeError):
        # URI hardcodeada como fallback
        mongo_uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
        logger.warning("Usando URI de MongoDB hardcodeada")

    try:
        logger.info(f"Conectando a MongoDB: {mongo_uri[:20]}...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        client.admin.command('ping')
        logger.info("Conexión a MongoDB establecida correctamente")

        # Determinar el nombre de la base de datos
        db_name = "app_catalogojoyero_nueva"
        if mongo_uri and "app_catalogojoyero_nueva" not in mongo_uri and "/" in mongo_uri:
            parts = mongo_uri.split("/")
            if len(parts) > 3:
                db_name_part = parts[3].split("?")[0]
                if db_name_part:
                    db_name = db_name_part

        logger.info(f"Usando base de datos: {db_name}")
        db = client[db_name]

        # Mostrar colecciones disponibles
        collections = db.list_collection_names()
        logger.info(f"Colecciones disponibles: {collections}")

        # Determinar la colección de usuarios
        user_collection = None
        if "users" in collections:
            user_collection = db.users
            logger.info("Usando colección 'users'")
        elif "usuarios" in collections:
            user_collection = db.usuarios
            logger.info("Usando colección 'usuarios'")
        else:
            user_collection = db.users
            logger.info("No se encontró colección de usuarios, usando 'users' por defecto")

        # Datos del usuario administrador
        admin_email = "admin@example.com"
        admin_password = "admin123"
        admin_pass_hash = generate_password_hash(admin_password)

        # Buscar si existe el administrador
        admin_user = user_collection.find_one({"email": admin_email})

        if admin_user:
            logger.info(f"Usuario administrador encontrado con ID: {admin_user.get('_id')}")

            # Actualizar contraseña
            try:
                user_collection.update_one(
                    {"email": admin_email},
                    {"$set": {
                        "password": admin_pass_hash,
                        "role": "admin",
                        "is_active": True,
                        "active": True,
                        "locked_until": None,
                        "failed_attempts": 0
                    }}
                )
                logger.info("Contraseña de administrador actualizada")
            except Exception as e:
                logger.error(f"Error al actualizar usuario: {str(e)}")

                # Intentar actualizar solo la contraseña como último recurso
                try:
                    user_collection.update_one(
                        {"email": admin_email},
                        {"$set": {"password": admin_pass_hash}}
                    )
                    logger.info("Sólo se actualizó la contraseña del administrador")
                except Exception as e2:
                    logger.error(f"Error también al actualizar solo la contraseña: {str(e2)}")
        else:
            logger.info("No se encontró usuario administrador, creándolo...")

            # Crear nuevo usuario administrador
            new_admin = {
                "email": admin_email,
                "password": admin_pass_hash,
                "username": "administrator",
                "nombre": "Administrador",
                "role": "admin",
                "is_active": True,
                "active": True,
                "failed_attempts": 0,
                "locked_until": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            try:
                result = user_collection.insert_one(new_admin)
                logger.info(f"Usuario administrador creado con ID: {result.inserted_id}")
            except Exception as e:
                logger.error(f"Error al crear usuario administrador: {str(e)}")

                # Intentar con un nombre de usuario único
                try:
                    import time
                    new_admin["username"] = f"admin_{int(time.time())}"
                    result = user_collection.insert_one(new_admin)
                    logger.info(f"Usuario administrador creado con username alternativo y ID: {result.inserted_id}")
                except Exception as e2:
                    logger.error(f"Error también con username alternativo: {str(e2)}")

        # Crear archivo HTML para acceso directo
        try:
            admin_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_direct.php")

            with open(admin_file, 'w') as f:
                f.write("""<?php
// Archivo admin_direct.php - Redirige al usuario directamente al panel de administración
header("Location: /login_directo");
exit();
?>
""")

            logger.info(f"Archivo de acceso directo creado: {admin_file}")
        except Exception as e:
            logger.error(f"Error al crear archivo de acceso directo: {str(e)}")

        # Mostrar instrucciones para acceso
        print("\n" + "=" * 60)
        print(" ACCESO ADMINISTRATIVO CONFIGURADO ".center(60))
        print("=" * 60)
        print("Credenciales de administrador:")
        print(f"  Email:    {admin_email}")
        print(f"  Password: {admin_password}")
        print("\nURL de acceso directo:")
        print("  https://edefrutos2025.xyz/admin_direct.php")
        print("\nURL de acceso normal:")
        print("  https://edefrutos2025.xyz/login")
        print("=" * 60)

        return 0
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
