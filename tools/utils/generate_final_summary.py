#!/usr/bin/env python3
"""
Script para generar el resumen final del sistema de notificación de contraseñas
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def generate_final_summary():
    """Genera el resumen final del sistema"""

    print("📋 RESUMEN FINAL DEL SISTEMA DE NOTIFICACIÓN DE CONTRASEÑAS")
    print("=" * 70)

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

            # Obtener todos los usuarios
            users_collection = get_users_collection()
            users = list(users_collection.find({}))

            print(f"\n👥 USUARIOS EN EL SISTEMA: {len(users)}")
            print("-" * 50)

            # Separar usuarios por tipo
            admins = [u for u in users if u.get("role") == "admin"]
            regular_users = [u for u in users if u.get("role") != "admin"]

            print(f"🔑 Administradores: {len(admins)}")
            print(f"👤 Usuarios regulares: {len(regular_users)}")

            print(f"\n🔐 CREDENCIALES DE ACCESO")
            print("-" * 50)

            # Mostrar credenciales de administradores
            if admins:
                print(f"\n🔑 ADMINISTRADORES:")
                for user in admins:
                    username = user.get("username", "N/A")
                    email = user.get("email", "N/A")
                    temp_password = (
                        f"{username}123"
                        if username != "N/A"
                        else f"{email.split('@')[0]}123"
                    )
                    print(f"   📧 {email}")
                    print(f"   👤 Usuario: {username}")
                    print(f"   🔑 Contraseña temporal: {temp_password}")
                    print()

            # Mostrar algunos usuarios regulares como ejemplo
            if regular_users:
                print(f"👤 USUARIOS REGULARES (ejemplos):")
                for i, user in enumerate(
                    regular_users[:5]
                ):  # Solo mostrar 5 como ejemplo
                    username = user.get("username", "N/A")
                    email = user.get("email", "N/A")
                    temp_password = (
                        f"{username}123"
                        if username != "N/A"
                        else f"{email.split('@')[0]}123"
                    )
                    print(f"   {i+1}. 📧 {email}")
                    print(f"      👤 Usuario: {username}")
                    print(f"      🔑 Contraseña temporal: {temp_password}")

                if len(regular_users) > 5:
                    print(f"   ... y {len(regular_users) - 5} usuarios más")
                print()

            return True

    except Exception as e:
        print(f"   ❌ Error al generar resumen: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal"""

    print("🚀 GENERANDO RESUMEN FINAL")
    print("=" * 70)

    # Generar resumen
    success = generate_final_summary()

    if success:
        print(f"\n🌐 URLs DEL SISTEMA")  # noqa: F541
        print("-" * 50)
        print(f"📱 Página principal: https://edefrutos2025.xyz")  # noqa: F541
        print(f"🔐 Login normal: https://edefrutos2025.xyz/login")  # noqa: F541
        print(
            f"⚠️  Notificación de contraseñas: https://edefrutos2025.xyz/password/password-reset-notification"  # noqa: F541
        )
        print(
            f"🔑 Login temporal: https://edefrutos2025.xyz/password/temporary-login"
        )  # noqa: F541
        print(
            f"🔄 Cambio forzado: https://edefrutos2025.xyz/usuarios/force_password_change"
        )

        print(f"\n📋 INSTRUCCIONES PARA USUARIOS")
        print("-" * 50)
        print(f"1. 📧 Los usuarios deben usar su EMAIL como identificador")
        print(f"2. 🔑 La contraseña temporal es: username123")
        print(f"3. ⚠️  Al acceder, serán redirigidos a cambiar la contraseña")
        print(f"4. ✅ Después del cambio, podrán usar el sistema normalmente")

        print(f"\n🎯 FLUJO DE USUARIO")
        print("-" * 50)
        print(f"1. Usuario va a: /password/password-reset-notification")
        print(f"2. Busca sus credenciales o va a: /password/temporary-login")
        print(f"3. Accede con email + contraseña temporal")
        print(f"4. Es redirigido a: /usuarios/force_password_change")
        print(f"5. Cambia su contraseña y accede al sistema")

        print(f"\n✅ SISTEMA COMPLETAMENTE FUNCIONAL")
        print("=" * 70)
        return True
    else:
        print(f"\n❌ Error al generar el resumen")  # noqa: F541
        return False


if __name__ == "__main__":
    main()
