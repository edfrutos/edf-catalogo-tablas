#!/usr/bin/env python3
# Script: verify_app_catalogojoyero.py
# Descripción: Verifica el estado de la base de datos app_catalogojoyero_nueva
# Uso: python3 verify_app_catalogojoyero.py
# Requiere: pymongo, certifi, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: EDF Developer - 2025-05-28

from pymongo import MongoClient
from pymongo.database import Database
import certifi
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()


def print_header(title: str) -> None:
    """Imprime un encabezado formateado"""
    print(f"\n{'=' * 60}")
    print(f"🔍 {title}")
    print(f"{'=' * 60}")


def print_success(message: str) -> None:
    """Imprime un mensaje de éxito"""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Imprime un mensaje de advertencia"""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Imprime un mensaje de error"""
    print(f"❌ {message}")


def print_info(message: str) -> None:
    """Imprime un mensaje informativo"""
    print(f"ℹ️  {message}")


def print_section(title: str) -> None:
    """Imprime una sección"""
    print(f"\n📋 {title}")
    print("-" * 40)


# Inicio del script
print_header("VERIFICADOR DE BASE DE DATOS")
print_info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print_info("Base de datos: app_catalogojoyero_nueva")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print_error("MONGO_URI no está definida en el entorno")
    exit(1)

try:
    client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["app_catalogojoyero_nueva"]

    # Verificar conexión
    client.admin.command("ping")
    print_success("Conexión a MongoDB establecida correctamente")

except Exception as e:
    print_error(f"Error al conectar con MongoDB: {e}")
    exit(1)

# Verificar usuario específico
print_section("VERIFICACIÓN DE USUARIO 'edefrutos'")
user = db["users"].find_one({"username": "edefrutos"})
if user:
    print_success(f"Usuario encontrado: {user['username']}")
    print_info(f"  • Rol: {user.get('role', 'No definido')}")
    print_info(f"  • Email: {user.get('email', 'No definido')}")
    print_info(f"  • ID: {user.get('_id')}")
    if user.get("created_at"):
        print_info(f"  • Creado: {user.get('created_at')}")
else:
    print_warning("Usuario 'edefrutos' no encontrado en la colección 'users'")

# Verificar colecciones
print_section("VERIFICACIÓN DE COLECCIONES")
colecciones = ["users", "catalogs", "spreadsheets"]
total_docs = 0

for col in colecciones:
    if col in db.list_collection_names():
        count = db[col].count_documents({})
        total_docs += count
        if count > 0:
            print_success(f"Colección '{col}': {count} documentos")
            # Mostrar ejemplo de documento de forma más limpia
            doc = db[col].find_one()
            if doc:
                print_info(f"  • Ejemplo de documento:")
                for key, value in list(doc.items())[:3]:  # Solo primeros 3 campos
                    if key != "_id":
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        print(f"    - {key}: {value_str}")
        else:
            print_warning(f"Colección '{col}' existe pero está vacía")
    else:
        print_error(f"Colección '{col}' NO EXISTE")

# Resumen final
print_header("RESUMEN DE VERIFICACIÓN")
print_info(f"Total de documentos en la base de datos: {total_docs}")
print_info("Verificación completada. Revisa los resultados arriba.")

# Cerrar conexión
client.close()
print_success("Conexión cerrada correctamente")
