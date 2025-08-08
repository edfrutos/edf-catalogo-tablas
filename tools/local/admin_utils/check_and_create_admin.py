#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: check_and_create_admin.py
Descripción: Verifica si existe un usuario admin y lo crea si no existe
Uso: python3 check_and_create_admin.py
Requiere: pymongo, dotenv
Variables de entorno: MONGO_URI
Autor: EDF Developer - 2025-01-27
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import hashlib
import secrets

# Cargar variables de entorno
load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ Error: Variable de entorno MONGO_URI no encontrada")
    print("Asegúrate de tener un archivo .env con las credenciales de MongoDB")
    sys.exit(1)


def create_admin_user():
    """Crea un usuario administrador si no existe."""
    try:
        # Conectar a MongoDB
        client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["app_catalogojoyero_nueva"]
        users_collection = db["users"]

        # Verificar si ya existe un usuario admin
        admin_user = users_collection.find_one({"role": "admin"})

        if admin_user:
            print(f"✅ Usuario admin ya existe:")
            print(f"   Usuario: {admin_user.get('username', 'N/A')}")
            print(f"   Email: {admin_user.get('email', 'N/A')}")
            print(f"   Rol: {admin_user.get('role', 'N/A')}")
            return True

        # Crear usuario admin
        admin_username = "admin"
        admin_email = "admin@edefrutos2025.xyz"
        admin_password = "admin123"  # Contraseña temporal

        # Generar salt y hash de la contraseña
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((admin_password + salt).encode()).hexdigest()

        # Crear documento del usuario
        admin_doc = {
            "username": admin_username,
            "email": admin_email,
            "password_hash": password_hash,
            "salt": salt,
            "role": "admin",
            "is_active": True,
            "created_at": "2025-01-27T00:00:00Z",
            "last_login": None,
        }

        # Insertar usuario admin
        result = users_collection.insert_one(admin_doc)

        if result.inserted_id:
            print("✅ Usuario admin creado exitosamente:")
            print(f"   Usuario: {admin_username}")
            print(f"   Email: {admin_email}")
            print(f"   Contraseña: {admin_password}")
            print(f"   ID: {result.inserted_id}")
            print("\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
            return True
        else:
            print("❌ Error: No se pudo crear el usuario admin")
            return False

    except Exception as e:
        print(f"❌ Error creando usuario admin: {e}")
        return False
    finally:
        if "client" in locals():
            client.close()


def check_database_connection():
    """Verifica la conexión a la base de datos."""
    try:
        client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["app_catalogojoyero_nueva"]

        # Verificar conexión
        client.admin.command("ping")
        print("✅ Conexión a MongoDB exitosa")

        # Verificar colección users
        users_collection = db["users"]
        user_count = users_collection.count_documents({})
        print(f"✅ Colección 'users' encontrada con {user_count} usuarios")

        return True

    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {e}")
        return False
    finally:
        if "client" in locals():
            client.close()


def main():
    """Función principal."""
    print("🔍 Verificando y configurando usuario administrador...")
    print("=" * 60)

    # Verificar conexión a la base de datos
    if not check_database_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return

    print()

    # Crear usuario admin si no existe
    if create_admin_user():
        print("\n🎉 Proceso completado exitosamente!")
        print("\n📋 Credenciales para acceder a /dev-template/testing/:")
        print("   URL: http://localhost:5000/dev-template/testing/")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("\n⚠️  Recuerda cambiar la contraseña después del primer login")
    else:
        print("\n❌ Error en el proceso de creación del usuario admin")


if __name__ == "__main__":
    main()
