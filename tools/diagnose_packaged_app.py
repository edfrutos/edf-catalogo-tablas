#!/usr/bin/env python3
"""
Script de diagnóstico para la aplicación empaquetada
"""

import os
import sys
import tempfile
from pathlib import Path
import requests
import time  # pyright: ignore[reportUnusedImport]


def check_environment():
    """Verificar el entorno de la aplicación"""
    print("🔍 Diagnóstico del entorno de la aplicación")
    print("=" * 50)

    # Verificar si estamos empaquetados
    is_frozen = getattr(sys, "frozen", False)
    print(f"📦 Aplicación empaquetada: {is_frozen}")

    if is_frozen:
        print(
            f"📁 Directorio base: {sys._MEIPASS}"  # pyright: ignore[reportAttributeAccessIssue]
        )
    else:
        print(f"📁 Directorio actual: {os.getcwd()}")

    # Verificar directorios críticos
    critical_dirs = ["app", "app/static", "app/templates", "app/routes"]

    print("\n📁 Verificando directorios críticos:")
    for dir_path in critical_dirs:
        if is_frozen:
            full_path = os.path.join(
                sys._MEIPASS, dir_path  # pyright: ignore[reportAttributeAccessIssue]
            )
        else:
            full_path = dir_path

        exists = os.path.exists(full_path)
        print(f"   {dir_path}: {'✅' if exists else '❌'}")
        if exists:
            try:
                files = len(os.listdir(full_path))
                print(f"      📄 {files} archivos")
            except Exception as e:
                print(f"      ❌ Error al listar: {e}")

    # Verificar archivos críticos
    critical_files = ["wsgi.py", "config.py", ".env", "requirements.txt"]

    print("\n📄 Verificando archivos críticos:")
    for file_path in critical_files:
        if is_frozen:
            full_path = os.path.join(
                sys._MEIPASS, file_path  # pyright: ignore[reportAttributeAccessIssue]
            )
        else:
            full_path = file_path

        exists = os.path.exists(full_path)
        print(f"   {file_path}: {'✅' if exists else '❌'}")
        if exists:
            try:
                size = os.path.getsize(full_path)
                print(f"      📏 {size} bytes")
            except Exception as e:
                print(f"      ❌ Error al verificar: {e}")


def check_permissions():
    """Verificar permisos de archivos"""
    print("\n🔐 Verificando permisos:")
    print("=" * 30)

    # Verificar directorio temporal
    temp_dir = Path(tempfile.gettempdir()) / "edf_catalogo_logs"
    print(f"📁 Directorio temporal: {temp_dir}")

    try:
        temp_dir.mkdir(exist_ok=True)
        print("   ✅ Directorio temporal creado/accesible")

        # Verificar permisos de escritura
        test_file = temp_dir / "test_write.txt"
        test_file.write_text("test")  # pyright: ignore[reportUnusedCallResult]
        test_file.unlink()
        print("   ✅ Permisos de escritura OK")

    except Exception as e:
        print(f"   ❌ Error con directorio temporal: {e}")

    # Verificar directorio de sesiones
    session_dir = temp_dir / "flask_session"
    try:
        session_dir.mkdir(exist_ok=True)
        print("   ✅ Directorio de sesiones OK")
    except Exception as e:
        print(f"   ❌ Error con directorio de sesiones: {e}")


def check_network():
    """Verificar conectividad de red"""
    print("\n🌐 Verificando conectividad:")
    print("=" * 30)

    # Verificar puerto local
    try:
        response = requests.get("http://127.0.0.1:5004", timeout=2)
        print(f"   ✅ Puerto 5004 accesible (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("   ❌ Puerto 5004 no accesible (servidor no iniciado)")
    except Exception as e:
        print(f"   ❌ Error al conectar: {e}")

    # Verificar puertos alternativos
    for port in [5000, 5001, 5002, 5003]:
        try:
            response = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            print(f"   ⚠️  Puerto {port} ocupado (status: {response.status_code})")
        except:
            pass


def check_imports():
    """Verificar importaciones críticas"""
    print("\n📚 Verificando importaciones:")
    print("=" * 30)

    critical_modules = [
        "flask",
        "flask_login",
        "pymongo",
        "webview",
        "requests",
        "threading",
        "tempfile",
        "pathlib",
    ]

    for module in critical_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")


def check_config():
    """Verificar configuración"""
    print("\n⚙️  Verificando configuración:")
    print("=" * 30)

    # Variables de entorno críticas
    env_vars = [
        "FLASK_ENV",
        "FLASK_DEBUG",
        "LOG_DIR",
        "FLASK_LOG_DIR",
        "SESSION_FILE_DIR",
    ]

    for var in env_vars:
        value = os.environ.get(var, "No definida")
        print(f"   {var}: {value}")


def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE APLICACIÓN EMPAQUETADA")
    print("=" * 60)

    try:
        check_environment()
        check_permissions()
        check_network()
        check_imports()
        check_config()

        print("\n✅ Diagnóstico completado")
        print("\n📋 Resumen:")
        print("   • Verifica que todos los directorios críticos existan")
        print("   • Asegúrate de que los permisos de escritura funcionen")
        print("   • Confirma que las importaciones críticas estén disponibles")
        print("   • Verifica que la configuración de entorno sea correcta")

    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
