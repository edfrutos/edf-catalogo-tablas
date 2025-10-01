#!/usr/bin/env python3
"""
Script para listar todos los usuarios disponibles
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()


def list_all_users():
    """Lista todos los usuarios disponibles"""
    print("👥 LISTANDO TODOS LOS USUARIOS DISPONIBLES")
    print("=" * 60)

    try:
        # Obtener MONGO_URI del archivo .env
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI no encontrado en .env")
            return False

        # Conectar directamente a MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_default_database()

        # Obtener todos los usuarios
        users = list(
            db.users.find(
                {},
                {
                    "email": 1,
                    "username": 1,
                    "nombre": 1,
                    "name": 1,
                    "role": 1,
                    "is_active": 1,
                    "active": 1,
                    "_id": 0,
                },
            )
        )

        print(f"📊 Total de usuarios encontrados: {len(users)}")
        print()

        # Mostrar usuarios activos primero
        active_users = [u for u in users if u.get("is_active", u.get("active", True))]
        inactive_users = [
            u for u in users if not u.get("is_active", u.get("active", True))
        ]

        print("✅ USUARIOS ACTIVOS:")
        print("-" * 40)
        for i, user in enumerate(active_users, 1):
            email = user.get("email", "N/A")
            username = user.get("username", "N/A")
            nombre = user.get("nombre", user.get("name", "N/A"))
            role = user.get("role", "user")

            print(f"{i:2d}. 📧 {email}")
            print(f"    👤 Username: {username}")
            print(f"    🏷️  Nombre: {nombre}")
            print(f"    🔑 Rol: {role}")
            print()

        if inactive_users:
            print("❌ USUARIOS INACTIVOS:")
            print("-" * 40)
            for i, user in enumerate(inactive_users, 1):
                email = user.get("email", "N/A")
                username = user.get("username", "N/A")
                nombre = user.get("nombre", user.get("name", "N/A"))
                role = user.get("role", "user")

                print(f"{i:2d}. 📧 {email}")
                print(f"    👤 Username: {username}")
                print(f"    🏷️  Nombre: {nombre}")
                print(f"    🔑 Rol: {role}")
                print()

        # Mostrar credenciales de prueba
        print("🔐 CREDENCIALES DE PRUEBA RECOMENDADAS:")
        print("-" * 40)
        print("📧 Email: edefrutos@edefrutos2025.xyz")
        print("🔑 Password: 15si34Maf")
        print("🔑 Rol: Admin")
        print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    list_all_users()
