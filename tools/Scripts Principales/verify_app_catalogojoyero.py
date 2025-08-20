#!/usr/bin/env python3
# Script: verify_app_catalogojoyero.py
# Descripción: Verifica la conexión y estado de la base de datos app_catalogojoyero_nueva
# Uso: python3 verify_app_catalogojoyero.py [opciones]
# Requiere: pymongo, certifi, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: Sistema de Verificación - 2025-05-28

import os
from typing import Optional

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database


# Colores para la salida
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(title: str) -> None:
    """Imprime un encabezado formateado"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}{Colors.END}")


def print_success(message: str) -> None:
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Imprime un mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str) -> None:
    """Imprime un mensaje informativo"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


# Cargar variables de entorno
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI no está definida en el entorno")

print_header("VERIFICACIÓN DE BASE DE DATOS")
print_info("Conectando a MongoDB...")

try:
    client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db: Database = client["app_catalogojoyero_nueva"]
    print_success("Conexión establecida correctamente")
except Exception as e:
    print_error(f"Error al conectar: {e}")
    exit(1)

print_header("VERIFICACIÓN DE USUARIO")
user: Optional[dict] = db["users"].find_one({"username": "edefrutos"})
if user:
    print_success(f"Usuario encontrado: {Colors.BOLD}{user['username']}{Colors.END}")
    print_info(f"  • Rol: {user.get('role', 'No definido')}")
    print_info(f"  • Email: {user.get('email', 'No definido')}")
    print_info(f"  • ID: {user.get('_id', 'No definido')}")
else:
    print_warning("Usuario 'edefrutos' no encontrado en la colección 'users'")

print_header("VERIFICACIÓN DE COLECCIONES")
colecciones = ["users", "catalogs", "spreadsheets"]
total_docs = 0

for col in colecciones:
    if col in db.list_collection_names():
        count = db[col].count_documents({})
        total_docs += count
        if count > 0:
            print_success(f"Colección '{col}': {count} documentos")
            # Mostrar ejemplo del primer documento
            doc = db[col].find_one()
            if doc:
                print_info(f"  • Ejemplo: {str(doc)[:100]}...")
        else:
            print_warning(f"Colección '{col}': Existe pero está vacía")
    else:
        print_error(f"Colección '{col}': No existe")

print_header("RESUMEN")
print_info(f"Total de documentos en todas las colecciones: {total_docs}")
print_info("Verificación completada exitosamente")

print(f"\n{Colors.BOLD}{Colors.GREEN}{'=' * 60}")
print("  VERIFICACIÓN FINALIZADA")
print(f"{'=' * 60}{Colors.END}")
