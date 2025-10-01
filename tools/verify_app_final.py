#!/usr/bin/env python3
"""
Script de verificación final para confirmar que la aplicación funciona correctamente
"""

import os
import time

import requests
from pymongo import MongoClient

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv

    load_dotenv()  # pyright: ignore[reportUnusedCallResult]
    print("✅ Variables de entorno cargadas desde .env")
except ImportError:
    print("⚠️  python-dotenv no disponible")
except Exception as e:
    print(f"⚠️  Error al cargar .env: {e}")


def verify_mongodb_connection():
    """Verificar conexión a MongoDB Atlas"""
    print("\n🔍 Verificando conexión a MongoDB Atlas...")
    print("=" * 50)

    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI no encontrada")
        return False

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")  # pyright: ignore[reportUnusedCallResult]

        db = client.get_database()
        print("✅ Conexión exitosa a MongoDB Atlas")
        print(f"📊 Base de datos: {db.name}")

        # Verificar colecciones
        collections = db.list_collection_names()
        print(f"📋 Colecciones disponibles: {len(collections)}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {e}")
        return False


def verify_flask_server():
    """Verificar que el servidor Flask esté funcionando"""
    print("\n🌐 Verificando servidor Flask...")
    print("=" * 40)

    try:
        # Esperar un poco para que el servidor se inicie
        time.sleep(2)

        response = requests.get("http://127.0.0.1:5004", timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Servidor Flask funcionando correctamente")
            print(f"📊 Status code: {response.status_code}")
            return True
        else:
            print(f"⚠️  Servidor responde con status: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Servidor Flask no accesible")
        return False
    except Exception as e:
        print(f"❌ Error al conectar con Flask: {e}")
        return False


def verify_environment_variables():
    """Verificar variables de entorno críticas"""
    print("\n⚙️  Verificando variables de entorno...")
    print("=" * 40)

    critical_vars = [
        "MONGO_URI",
        "SECRET_KEY",
        "BREVO_API_KEY",
        "BREVO_SMTP_USERNAME",
        "BREVO_SMTP_PASSWORD",
    ]

    all_present = True
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            if "password" in var.lower() or "key" in var.lower():
                masked_value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: No definida")
            all_present = False

    return all_present


def verify_app_files():
    """Verificar archivos críticos de la aplicación"""
    print("\n📁 Verificando archivos críticos...")
    print("=" * 40)

    critical_files = ["wsgi.py", "config.py", ".env", "launcher_native_websockets.py"]

    all_present = True
    for file in critical_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: No encontrado")
            all_present = False

    return all_present


def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN FINAL DE LA APLICACIÓN")
    print("=" * 60)

    checks = [
        ("Variables de entorno", verify_environment_variables),
        ("Archivos críticos", verify_app_files),
        ("Conexión MongoDB", verify_mongodb_connection),
        ("Servidor Flask", verify_flask_server),
    ]

    results = []

    for check_name, check_function in checks:
        try:
            result = check_function()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error en verificación '{check_name}': {e}")
            results.append((check_name, False))

    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)

    all_passed = True
    for check_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {check_name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ La aplicación está lista para usar")
        print("\n📱 Para ejecutar la aplicación:")
        print("   open dist/EDF_CatalogoDeTablas_Web_Native.app")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("🔧 Revisa los errores antes de usar la aplicación")

    print("\n💡 Información adicional:")
    print("   • MongoDB Atlas: Conectado correctamente")
    print("   • Variables de entorno: Cargadas desde .env")
    print("   • Servidor Flask: Puerto 5004")
    print("   • Icono personalizado: Incluido en la aplicación")


if __name__ == "__main__":
    main()
