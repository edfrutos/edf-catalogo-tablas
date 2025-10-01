#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de MongoDB en la aplicación macOS
Autor: EDF Developer - 2025
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_environment():
    """Verifica el entorno de la aplicación"""
    print("🔍 VERIFICANDO ENTORNO DE LA APLICACIÓN")
    print("=" * 50)

    # Verificar si estamos en una aplicación empaquetada
    if getattr(sys, "frozen", False):
        print("✅ Aplicación empaquetada detectada")
        app_path = os.path.dirname(sys.executable)
        print(f"📁 Ruta de la aplicación: {app_path}")
    else:
        print("ℹ️  Ejecutando en modo desarrollo")
        app_path = os.getcwd()

    # Verificar archivo .env
    env_path = os.path.join(app_path, ".env")
    if os.path.exists(env_path):
        print("✅ Archivo .env encontrado")
        try:
            with open(env_path, "r") as f:
                content = f.read()
                if "MONGO_URI" in content:
                    print("✅ MONGO_URI encontrada en .env")
                else:
                    print("❌ MONGO_URI no encontrada en .env")
        except Exception as e:
            print(f"❌ Error leyendo .env: {e}")
    else:
        print("❌ Archivo .env no encontrado")

    # Verificar variables de entorno
    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        print("✅ MONGO_URI en variables de entorno")
        # Mostrar solo la parte segura de la URI
        safe_uri = (
            mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri[:30] + "..."
        )
        print(f"📡 URI: {safe_uri}")
    else:
        print("❌ MONGO_URI no está en variables de entorno")

    return mongo_uri


def test_mongodb_connection(mongo_uri):
    """Prueba la conexión a MongoDB"""
    print("\n🔍 PROBANDO CONEXIÓN A MONGODB")
    print("=" * 50)

    if not mongo_uri:
        print("❌ No hay URI de MongoDB para probar")
        return False

    try:
        import certifi
        import pymongo

        print("📡 Intentando conectar a MongoDB...")

        # Configuración optimizada para aplicaciones empaquetadas
        config = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 30000,
            "maxPoolSize": 5,
            "minPoolSize": 1,
            "maxIdleTimeMS": 30000,
            "waitQueueTimeoutMS": 5000,
        }

        # Agregar configuración SSL si es necesario
        if mongo_uri.startswith("mongodb+srv://"):
            config["tlsCAFile"] = certifi.where()
            print("🔒 Configuración SSL habilitada para MongoDB Atlas")

        client = pymongo.MongoClient(mongo_uri, **config)

        # Probar conexión con ping
        result = client.admin.command("ping")
        print(f"✅ Conexión exitosa: {result}")

        # Obtener información de la base de datos
        db = client.get_database()
        print(f"📊 Base de datos: {db.name}")

        # Listar colecciones
        collections = db.list_collection_names()
        print(f"📋 Colecciones disponibles: {len(collections)}")
        for coll in collections[:5]:  # Mostrar solo las primeras 5
            print(f"   - {coll}")

        # Verificar colección de usuarios
        if "users" in collections:
            users_count = db.users.count_documents({})
            print(f"👥 Usuarios en la base de datos: {users_count}")

            # Buscar usuario admin
            admin_user = db.users.find_one({"role": "admin"})
            if admin_user:
                print(f"👤 Usuario admin encontrado: {admin_user.get('email', 'N/A')}")
            else:
                print("⚠️  No se encontró usuario admin")
        else:
            print("❌ Colección 'users' no encontrada")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def check_network_connectivity():
    """Verifica la conectividad de red"""
    print("\n🌐 VERIFICANDO CONECTIVIDAD DE RED")
    print("=" * 50)

    # Probar conectividad básica
    test_hosts = [("google.com", 80), ("cloud.mongodb.com", 443), ("8.8.8.8", 53)]

    for host, port in test_hosts:
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"✅ {host}:{port} - Conectividad OK")
            else:
                print(f"❌ {host}:{port} - Sin conectividad")
        except Exception as e:
            print(f"❌ {host}:{port} - Error: {e}")


def check_ssl_certificates():
    """Verifica los certificados SSL"""
    print("\n🔒 VERIFICANDO CERTIFICADOS SSL")
    print("=" * 50)

    try:
        import certifi

        cert_path = certifi.where()
        if os.path.exists(cert_path):
            print(f"✅ Certificados SSL encontrados: {cert_path}")

            # Verificar tamaño del archivo
            size = os.path.getsize(cert_path)
            print(f"📏 Tamaño del archivo: {size:,} bytes")

            if size > 0:
                print("✅ Archivo de certificados válido")
            else:
                print("❌ Archivo de certificados vacío")
        else:
            print("❌ Archivo de certificados no encontrado")

    except Exception as e:
        print(f"❌ Error verificando certificados: {e}")


def check_python_environment():
    """Verifica el entorno de Python"""
    print("\n🐍 VERIFICANDO ENTORNO DE PYTHON")
    print("=" * 50)

    print(f"📦 Python versión: {sys.version}")
    print(f"📁 Directorio de trabajo: {os.getcwd()}")

    # Verificar módulos necesarios
    required_modules = ["pymongo", "certifi", "flask", "flask_login"]

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - Disponible")
        except ImportError:
            print(f"❌ {module} - No disponible")


def check_application_logs():
    """Verifica los logs de la aplicación"""
    print("\n📋 VERIFICANDO LOGS DE LA APLICACIÓN")
    print("=" * 50)

    # Buscar archivos de log
    log_dirs = ["logs", "app_data/logs", "."]
    log_files = []

    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith(".log"):
                    log_files.append(os.path.join(log_dir, file))

    if log_files:
        print(f"📄 Archivos de log encontrados: {len(log_files)}")
        for log_file in log_files[:3]:  # Mostrar solo los primeros 3
            print(f"   - {log_file}")

            # Buscar errores de MongoDB en el último log
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    mongo_errors = [
                        line
                        for line in lines[-50:]
                        if "mongodb" in line.lower() or "mongo" in line.lower()
                    ]
                    if mongo_errors:
                        print(
                            f"   ⚠️  Errores de MongoDB encontrados en {os.path.basename(log_file)}:"
                        )
                        for error in mongo_errors[-3:]:  # Últimos 3 errores
                            print(f"      {error.strip()}")
            except Exception as e:
                print(f"   ❌ Error leyendo {log_file}: {e}")
    else:
        print("ℹ️  No se encontraron archivos de log")


def generate_report():
    """Genera un reporte completo"""
    print("\n📊 GENERANDO REPORTE DE DIAGNÓSTICO")
    print("=" * 50)

    report = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "frozen": getattr(sys, "frozen", False),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
        },
        "mongodb": {
            "uri_configured": bool(os.environ.get("MONGO_URI")),
            "connection_test": None,
        },
        "network": {},
        "ssl": {},
        "logs": {},
    }

    # Probar conexión MongoDB
    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        try:
            import certifi
            import pymongo

            config = {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
            }

            if mongo_uri.startswith("mongodb+srv://"):
                config["tlsCAFile"] = certifi.where()

            client = pymongo.MongoClient(mongo_uri, **config)
            client.admin.command("ping")
            client.close()

            report["mongodb"]["connection_test"] = True
        except Exception as e:
            report["mongodb"]["connection_test"] = False
            report["mongodb"]["error"] = str(e)

    # Guardar reporte
    report_file = (
        f"mongodb_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    try:
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Reporte guardado: {report_file}")
    except Exception as e:
        print(f"❌ Error guardando reporte: {e}")


def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO MONGODB PARA APLICACIÓN MACOS")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Verificar entorno
        mongo_uri = check_environment()

        # Verificar conectividad de red
        check_network_connectivity()

        # Verificar certificados SSL
        check_ssl_certificates()

        # Verificar entorno Python
        check_python_environment()

        # Verificar logs
        check_application_logs()

        # Probar conexión MongoDB
        if mongo_uri:
            connection_ok = test_mongodb_connection(mongo_uri)
            if connection_ok:
                print("\n🎉 ¡DIAGNÓSTICO COMPLETADO!")
                print("✅ La conexión a MongoDB está funcionando correctamente")
                print("💡 Si sigues teniendo problemas, verifica:")
                print("   - La configuración de la aplicación")
                print("   - Los permisos de red")
                print("   - La configuración del firewall")
            else:
                print("\n❌ PROBLEMAS DETECTADOS")
                print("🔧 Recomendaciones:")
                print("   1. Verifica la URI de MongoDB")
                print("   2. Confirma la conectividad de red")
                print("   3. Revisa los certificados SSL")
                print("   4. Consulta los logs de la aplicación")
        else:
            print("\n⚠️  CONFIGURACIÓN INCOMPLETA")
            print("🔧 Necesitas configurar MONGO_URI en el archivo .env")

        # Generar reporte
        generate_report()

    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
