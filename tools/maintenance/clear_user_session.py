#!/usr/bin/env python3
"""
Script para limpiar la sesión de un usuario específico
y resetear sus flags si es necesario.
"""

import sys
from datetime import datetime
from pathlib import Path

# Agregar la ruta raíz del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

# Importar funciones de la aplicación
from app.models.database import get_users_collection  # noqa: E402


def clear_user_flags(username):
    """
    Limpia los flags de contraseña temporal de un usuario específico.
    """
    print(f"🧹 Limpiando flags de usuario: {username}")

    try:
        users_collection = get_users_collection()

        # Buscar el usuario
        user = users_collection.find_one({"username": username})
        if not user:
            print(f"❌ Usuario {username} no encontrado")
            return False

        print(f"📋 Usuario encontrado: {user.get('email')}")

        # Verificar estado actual
        current_flags = {
            "temp_password": user.get("temp_password", False),
            "must_change_password": user.get("must_change_password", False),
            "password_reset_required": user.get("password_reset_required", False),
        }

        print("🔍 Estado actual de flags:")
        for flag, value in current_flags.items():
            print(f"   - {flag}: {value}")

        # Si ya están limpiados, no hacer nada
        if not any(current_flags.values()):
            print("✅ Los flags ya están limpiados - no se requiere acción")
            return True

        # Limpiar los flags
        result = users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "temp_password": False,
                    "must_change_password": False,
                    "password_reset_required": False,
                    "flags_cleared_at": datetime.utcnow().isoformat(),
                    "flags_cleared_manually": True,
                }
            },
        )

        if result.modified_count > 0:
            print(f"✅ Flags limpiados correctamente para {username}")
            print("💡 El usuario ya no será redirigido al cambio de contraseña")
            return True
        else:
            print(f"⚠️ No se pudieron limpiar los flags para {username}")
            return False

    except Exception as e:
        print(f"❌ Error limpiando flags: {str(e)}")
        return False


def show_user_status(username):
    """
    Muestra el estado actual de un usuario.
    """
    try:
        users_collection = get_users_collection()
        user = users_collection.find_one({"username": username})

        if not user:
            print(f"❌ Usuario {username} no encontrado")
            return

        print(f"📋 Estado del usuario: {username}")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        print(f"   temp_password: {user.get('temp_password', False)}")
        print(f"   must_change_password: {user.get('must_change_password', False)}")
        print(
            f"   password_reset_required: {user.get('password_reset_required', False)}"
        )

        if user.get("flags_cleared_at"):
            print(f"   Flags limpiados: {user.get('flags_cleared_at')}")

    except Exception as e:
        print(f"❌ Error obteniendo estado: {str(e)}")


if __name__ == "__main__":
    print("🔧 Herramienta de Limpieza de Sesión de Usuario")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Uso: python clear_user_session.py <username> [clear]")
        print("\nEjemplos:")
        print("  python clear_user_session.py rocio        # Ver estado")
        print("  python clear_user_session.py rocio clear  # Limpiar flags")
        sys.exit(1)

    username = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "status"

    if action == "clear":
        clear_user_flags(username)
    else:
        show_user_status(username)
