#!/usr/bin/env python3
"""
Script para listar todos los usuarios y sus contraseñas
"""

import os
import sys

from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def list_all_users():
    """Lista todos los usuarios y sus contraseñas"""

    print("👥 LISTANDO TODOS LOS USUARIOS")
    print("=" * 60)

    # Cargar variables de entorno
    load_dotenv()

    try:
        # Importar la aplicación Flask
        from main_app import create_app

        # Crear la aplicación
        app = create_app()

        with app.app_context():
            # Importar funciones necesarias
            from app.models import get_users_collection

            # Obtener colección de usuarios
            users_collection = get_users_collection()

            # Obtener todos los usuarios
            all_users = list(
                users_collection.find(
                    {},
                    {
                        "email": 1,
                        "username": 1,
                        "nombre": 1,
                        "role": 1,
                        "password_type": 1,
                        "_id": 1,
                    },
                ).sort("email", 1)
            )

            print(f"   📊 Total de usuarios: {len(all_users)}")

            print("\n" + "=" * 50)
            print("LISTA COMPLETA DE USUARIOS")
            print("=" * 50)

            for i, user in enumerate(all_users, 1):
                email = user.get("email", "N/A")
                username = user.get("username", "N/A")
                nombre = user.get("nombre", "N/A")
                role = user.get("role", "user")
                password_type = user.get("password_type", "unknown")

                print(f"   {i:2d}. {email}")
                print(f"       - Usuario: {username}")
                print(f"       - Nombre: {nombre}")
                print(f"       - Rol: {role}")
                print(f"       - Tipo contraseña: {password_type}")

                # Sugerir contraseña basada en username
                if username and username != "N/A":
                    suggested_password = f"{username}123"
                else:
                    suggested_password = "password123"

                print(f"       - Contraseña sugerida: {suggested_password}")
                print()

            # Mostrar resumen por roles
            print("\n" + "=" * 50)
            print("RESUMEN POR ROLES")
            print("=" * 50)

            admin_users = [u for u in all_users if u.get("role") == "admin"]
            regular_users = [u for u in all_users if u.get("role") == "user"]

            print(f"   👑 Administradores: {len(admin_users)}")
            for user in admin_users:
                email = user.get("email", "N/A")
                username = user.get("username", "N/A")
                suggested_password = (
                    f"{username}123" if username != "N/A" else "admin123"
                )
                print(f"      - {email} / {suggested_password}")

            print(f"\n   👤 Usuarios regulares: {len(regular_users)}")
            for user in regular_users:
                email = user.get("email", "N/A")
                username = user.get("username", "N/A")
                suggested_password = (
                    f"{username}123" if username != "N/A" else "user123"
                )
                print(f"      - {email} / {suggested_password}")

            return True

    except Exception as e:
        print(f"   ❌ Error listando usuarios: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal"""

    print("🚀 LISTANDO TODOS LOS USUARIOS")
    print("=" * 60)

    # Ejecutar listado
    success = list_all_users()

    if success:
        print("\n🎉 Listado completado")
        return True
    else:
        print("\n❌ El listado no se completó correctamente")
        return False


if __name__ == "__main__":
    main()
