#!/usr/bin/env python3

# Script: show_admin_user.py
# Descripción: [Localizar usuario administrador, previamente identificado en el script]
# Uso: python3 show_admin_user.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-05

from app.models import get_users_collection
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient

# Agregar el directorio raíz al path para poder importar app
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
db_name = os.getenv("MONGODB_DB", "app_catalogojoyero_nueva")
COLLECTION = "users"

client: MongoClient = MongoClient(MONGO_URI)
db = client[db_name]
users = get_users_collection()

admin = users.find_one({"email": "edfrutos@gmail.com"})

if admin:
    print("=" * 60)
    print("🔍 INFORMACIÓN DEL USUARIO ADMINISTRADOR")
    print("=" * 60)
    print(f"📧 Email: {admin.get('email', 'No especificado')}")
    print(f"👤 Nombre: {admin.get('name', 'No especificado')}")
    print(f"🏷️  Rol: {admin.get('role', 'No especificado')}")
    print(f"📅 Fecha de creación: {admin.get('created_at', 'No especificado')}")
    print(f"🔄 Última actualización: {admin.get('updated_at', 'No especificado')}")
    print(f"✅ Activo: {'Sí' if admin.get('is_active', False) else 'No'}")
    print(
        f"🔐 2FA habilitado: {'Sí' if admin.get('two_factor_enabled', False) else 'No'}"
    )
    print("=" * 60)

    # Información adicional en formato detallado
    print("\n📋 DETALLES COMPLETOS DEL USUARIO:")
    print("-" * 40)
    for key, value in admin.items():
        if key not in ["_id", "password"]:  # Excluir campos sensibles
            formatted_key = key.replace("_", " ").title()
            print(f"  • {formatted_key}: {value}")
else:
    print("❌ No se encontró el usuario administrador con email: edfrutos@gmail.com")
    print("💡 Verifica que el usuario existe en la base de datos.")
