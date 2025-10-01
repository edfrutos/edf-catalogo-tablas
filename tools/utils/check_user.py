#!/usr/bin/env python3
"""
Script para verificar los datos del usuario y permisos de administrador
"""
from app.database import get_users_collection, initialize_db
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_user_permissions():
    print("Iniciando verificación de usuario...")

    # Inicializar conexión a la base de datos
    try:
        # Inicializar conexión sin app Flask
        print("Inicializando conexión a la base de datos...")
        if initialize_db():
            print("✅ Conexión a MongoDB establecida")
        else:
            print("❌ Error conectando a MongoDB")
            return
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return

    # Obtener colección de usuarios
    try:
        users_collection = get_users_collection()
        if users_collection is None:
            print("❌ No se pudo obtener la colección de usuarios")
            return

        # Buscar usuario edefrutos
        user = users_collection.find_one({"username": "edefrutos"})
        if not user:
            print("❌ Usuario 'edefrutos' no encontrado")
            return

        print(f"✅ Usuario encontrado: {user.get('username')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        print(f"   Is Active: {user.get('is_active')}")
        print(f"   Is Admin: {user.get('is_admin')}")

        # Verificar si necesita actualización
        if user.get("role") == "admin" and not user.get("is_admin"):
            print("\n⚠️  El usuario tiene role='admin' pero is_admin=False")
            print("   Actualizando is_admin=True...")

            result = users_collection.update_one(
                {"username": "edefrutos"}, {"$set": {"is_admin": True}}
            )

            if result.modified_count > 0:
                print("✅ Usuario actualizado correctamente")
            else:
                print("❌ Error actualizando usuario")

        elif user.get("is_admin"):
            print("✅ Usuario tiene permisos de administrador correctos")

        else:
            print("❌ Usuario no tiene permisos de administrador")
            print("   Actualizando permisos de administrador...")

            result = users_collection.update_one(
                {"username": "edefrutos"}, {"$set": {"is_admin": True, "role": "admin"}}
            )

            if result.modified_count > 0:
                print("✅ Permisos de administrador otorgados")
            else:
                print("❌ Error otorgando permisos de administrador")

    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")


if __name__ == "__main__":
    check_user_permissions()
