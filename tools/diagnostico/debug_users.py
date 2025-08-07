#!/usr/bin/env python3
# Script: debug_users.py
# Descripción: [Datos principales del usuario (username, email, role, etc.)]
# Uso: python3 debug_users.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Cargar variables de entorno desde .env
load_dotenv()


# Colores para la salida
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(title):
    """Imprime un encabezado formateado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}{Colors.ENDC}\n")


def print_section(title):
    """Imprime una sección formateada"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}📋 {title}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * (len(title) + 4)}{Colors.ENDC}")


def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_warning(message):
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_error(message):
    """Imprime un mensaje de error"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message):
    """Imprime un mensaje informativo"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def format_user_data(user):
    """Formatea los datos del usuario para una mejor presentación"""
    # Campos sensibles que no mostrar
    sensitive_fields = ["password", "password_updated_at"]

    formatted_user = {}
    for key, value in user.items():
        if key not in sensitive_fields:
            if isinstance(value, datetime):
                formatted_user[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_user[key] = value

    return formatted_user


def print_user_table(users, search_criteria):
    """Imprime una tabla formateada de usuarios"""
    if not users:
        print_warning(f"No se encontraron usuarios con {search_criteria}")
        return

    print(f"\n{Colors.BOLD}🔍 Resultados para: {search_criteria}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'─' * 80}{Colors.ENDC}")

    for i, user in enumerate(users, 1):
        formatted_user = format_user_data(user)
        print(f"\n{Colors.BOLD}Usuario #{i}:{Colors.ENDC}")

        # Organizar campos en grupos lógicos
        basic_info = {
            k: v
            for k, v in formatted_user.items()
            if k in ["username", "email", "nombre", "role", "active", "verified"]
        }
        security_info = {
            k: v
            for k, v in formatted_user.items()
            if k in ["failed_attempts", "locked_until", "last_ip", "last_login"]
        }
        other_info = {
            k: v
            for k, v in formatted_user.items()
            if k not in basic_info and k not in security_info
        }

        # Información básica
        print(f"  {Colors.OKGREEN}📝 Información Básica:{Colors.ENDC}")
        for key, value in basic_info.items():
            status_icon = (
                "✅" if value in [True, "admin"] else "❌" if value is False else "📄"
            )
            print(f"    {status_icon} {key}: {value}")

        # Información de seguridad
        if security_info:
            print(f"  {Colors.WARNING}🔒 Información de Seguridad:{Colors.ENDC}")
            for key, value in security_info.items():
                if value is not None:
                    print(f"    🔐 {key}: {value}")

        # Otra información
        if other_info:
            print(f"  {Colors.OKCYAN}📋 Información Adicional:{Colors.ENDC}")
            for key, value in other_info.items():
                print(f"    📄 {key}: {value}")

        print(f"{Colors.OKCYAN}{'─' * 40}{Colors.ENDC}")


def main():
    """Función principal del script"""
    print_header("🔍 DIAGNÓSTICO DE USUARIOS - MONGODB")

    # Verificar conexión a MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print_error("MONGO_URI no está definida en el entorno")
        return

    try:
        client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        # Verificar conexión
        client.admin.command("ping")
        print_success("Conexión a MongoDB establecida correctamente")
    except Exception as e:
        print_error(f"Error al conectar con MongoDB: {e}")
        return

    # Obtener bases de datos
    print_section("BASES DE DATOS DISPONIBLES")
    databases = client.list_database_names()

    if not databases:
        print_warning("No se encontraron bases de datos")
        return

    print_info(f"Se encontraron {len(databases)} bases de datos:")
    for db_name in databases:
        print(f"  📊 {db_name}")

    # Buscar usuarios en cada base de datos
    total_users_found = 0

    for db_name in databases:
        print_section(f"ANÁLISIS DE BASE DE DATOS: {db_name.upper()}")

        db = client[db_name]
        collections = db.list_collection_names()

        if "users" not in collections:
            print_warning(f"Colección 'users' no encontrada en {db_name}")
            continue

        print_success(f"Colección 'users' encontrada en {db_name}")
        users_collection = db["users"]

        # Contar total de usuarios
        total_users = users_collection.count_documents({})
        print_info(f"Total de usuarios en la colección: {total_users}")

        # Buscar usuarios específicos
        search_criteria = [
            ("username", "edefrutos"),
            ("email", "edfrutos@gmail.com"),
            ("nombre", "edefrutos"),
        ]

        for field, value in search_criteria:
            users = list(users_collection.find({field: value}))
            if users:
                total_users_found += len(users)
                print_user_table(users, f"{field}='{value}'")

    # Resumen final
    print_header("📊 RESUMEN DEL DIAGNÓSTICO")
    print_success(f"Análisis completado en {len(databases)} bases de datos")
    print_info(f"Total de usuarios encontrados: {total_users_found}")

    if total_users_found > 0:
        print_success(
            "Se encontraron usuarios que coinciden con los criterios de búsqueda"
        )
    else:
        print_warning(
            "No se encontraron usuarios que coincidan con los criterios de búsqueda"
        )

    print(f"\n{Colors.HEADER}{Colors.BOLD}🏁 Diagnóstico completado{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
