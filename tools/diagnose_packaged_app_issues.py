#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas de la aplicación empaquetada
"""

import json  # pyright: ignore[reportUnusedImport]
import os
import subprocess  # pyright: ignore[reportUnusedImport]
import sys
import tempfile
import time  # pyright: ignore[reportUnusedImport]
from pathlib import Path

import requests


def check_app_launch():
    """Verificar si la aplicación se puede lanzar"""
    print("🚀 Verificando lanzamiento de la aplicación...")
    print("=" * 50)

    app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"

    if not os.path.exists(app_path):
        print(f"❌ Aplicación no encontrada: {app_path}")
        return False

    print(f"✅ Aplicación encontrada: {app_path}")

    # Verificar estructura de la aplicación
    contents_path = os.path.join(app_path, "Contents")
    if not os.path.exists(contents_path):
        print("❌ Estructura de aplicación incorrecta")
        return False

    # Verificar ejecutable
    executable_path = os.path.join(
        contents_path, "MacOS", "EDF_CatalogoDeTablas_Web_Native"
    )
    if not os.path.exists(executable_path):
        print("❌ Ejecutable no encontrado")
        return False

    print("✅ Estructura de aplicación correcta")
    return True


def check_icon():
    """Verificar icono de la aplicación"""
    print("\n🎨 Verificando icono de la aplicación...")
    print("=" * 40)

    # Verificar archivo de icono
    icon_path = (
        "dist/EDF_CatalogoDeTablas_Web_Native.app/Contents/Resources/edf_developer.icns"
    )
    if os.path.exists(icon_path):
        size = os.path.getsize(icon_path)
        print(f"✅ Icono encontrado: {icon_path} ({size} bytes)")
    else:
        print(f"❌ Icono no encontrado: {icon_path}")

    # Verificar configuración en Info.plist
    info_plist_path = "dist/EDF_CatalogoDeTablas_Web_Native.app/Contents/Info.plist"
    if os.path.exists(info_plist_path):
        try:
            with open(info_plist_path, "r") as f:
                content = f.read()
                if "edf_developer.icns" in content:
                    print("✅ Icono configurado en Info.plist")
                else:
                    print("❌ Icono no configurado en Info.plist")
        except Exception as e:
            print(f"❌ Error al leer Info.plist: {e}")
    else:
        print("❌ Info.plist no encontrado")


def check_server_startup():
    """Verificar inicio del servidor"""
    print("\n🌐 Verificando inicio del servidor...")
    print("=" * 40)

    # Intentar iniciar el servidor manualmente
    try:
        # Cambiar al directorio de la aplicación
        app_resources = "dist/EDF_CatalogoDeTablas_Web_Native.app/Contents/Resources"
        if os.path.exists(app_resources):
            os.chdir(app_resources)
            print(f"📁 Cambiado a directorio: {os.getcwd()}")

            # Verificar archivos críticos
            critical_files = ["wsgi.py", "config.py", ".env"]
            for file in critical_files:
                if os.path.exists(file):
                    print(f"✅ {file} encontrado")
                else:
                    print(f"❌ {file} no encontrado")

            # Intentar importar wsgi
            try:
                sys.path.insert(0, app_resources)
                from wsgi import app

                print("✅ Módulo wsgi importado correctamente")

                # Verificar configuración de la app
                if hasattr(app, "config"):
                    print("✅ Configuración de Flask disponible")
                else:
                    print("❌ Configuración de Flask no disponible")

            except ImportError as e:
                print(f"❌ Error al importar wsgi: {e}")
            except Exception as e:
                print(f"❌ Error al cargar aplicación: {e}")

        else:
            print("❌ Directorio de recursos no encontrado")

    except Exception as e:
        print(f"❌ Error al verificar servidor: {e}")


def check_network_access():
    """Verificar acceso de red"""
    print("\n🌐 Verificando acceso de red...")
    print("=" * 40)

    # Verificar puerto 5004
    try:
        response = requests.get("http://127.0.0.1:5004", timeout=2)
        print(f"✅ Puerto 5004 accesible (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Puerto 5004 no accesible")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")

    # Verificar otros puertos
    for port in [5000, 5001, 5002, 5003, 5005]:
        try:
            response = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            print(f"⚠️  Puerto {port} ocupado (status: {response.status_code})")
        except BaseException:
            pass

    return False


def check_permissions():
    """Verificar permisos de la aplicación"""
    print("\n🔐 Verificando permisos...")
    print("=" * 30)

    app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"

    # Verificar permisos de ejecución
    executable_path = os.path.join(
        app_path, "Contents", "MacOS", "EDF_CatalogoDeTablas_Web_Native"
    )
    if os.path.exists(executable_path):
        if os.access(executable_path, os.X_OK):
            print("✅ Permisos de ejecución OK")
        else:
            print("❌ Sin permisos de ejecución")
            print("💡 Ejecuta: chmod +x " + executable_path)

    # Verificar permisos de escritura en directorio temporal
    temp_dir = Path.home() / "Library" / "Logs" / "EDF_Catalogo"
    try:
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / "test_permissions.txt"
        test_file.write_text("test")  # pyright: ignore[reportUnusedCallResult]
        test_file.unlink()
        print("✅ Permisos de escritura en directorio temporal OK")
    except Exception as e:
        print(f"❌ Error con permisos de escritura: {e}")


def check_dependencies():
    """Verificar dependencias"""
    print("\n📦 Verificando dependencias...")
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

    missing_modules = []
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n⚠️  Módulos faltantes: {', '.join(missing_modules)}")
    else:
        print("\n✅ Todas las dependencias críticas disponibles")


def check_logs():
    """Verificar logs de la aplicación"""
    print("\n📝 Verificando logs...")
    print("=" * 30)

    # Buscar logs recientes
    log_dirs = [
        Path.home() / "Library" / "Logs" / "EDF_Catalogo",
        Path.home() / "Library" / "Logs",
        Path.cwd() / "logs",
    ]

    for log_dir in log_dirs:
        if log_dir.exists():
            print(f"📁 Directorio de logs encontrado: {log_dir}")
            try:
                log_files = list(log_dir.glob("*.log"))
                if log_files:
                    for log_file in log_files[-3:]:  # Últimos 3 archivos
                        print(f"   📄 {log_file.name}")
                        # Mostrar últimas líneas del log
                        try:
                            with open(log_file, "r") as f:
                                lines = f.readlines()
                                if lines:
                                    last_line = lines[-1].strip()
                                    print(f"      Última línea: {last_line[:100]}...")
                        except Exception as e:
                            print(f"      ❌ Error al leer log: {e}")
                else:
                    print("   📄 No hay archivos de log")
            except Exception as e:
                print(f"   ❌ Error al listar logs: {e}")


def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE PROBLEMAS DE APLICACIÓN EMPAQUETADA")
    print("=" * 70)

    try:
        # Verificaciones básicas
        if not check_app_launch():
            print("\n❌ Problema crítico: No se puede lanzar la aplicación")
            return

        check_icon()
        check_permissions()
        check_dependencies()

        # Verificaciones de red
        if check_network_access():
            print("\n✅ Servidor funcionando correctamente")
        else:
            print("\n⚠️  Servidor no accesible - verificando logs...")
            check_logs()

        # Verificación de servidor
        check_server_startup()

        print("\n" + "=" * 70)
        print("📋 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 70)
        print("✅ Verificaciones completadas")
        print("\n💡 Si hay problemas:")
        print("   1. Verifica que la aplicación tenga permisos de ejecución")
        print("   2. Revisa los logs en el directorio temporal")
        print("   3. Asegúrate de que el puerto 5004 esté libre")
        print("   4. Verifica que todas las dependencias estén incluidas")
        print("\n🔧 Para más información:")
        print("   - Ejecuta la aplicación desde terminal para ver errores")
        print("   - Revisa los logs del sistema")
        print("   - Verifica la configuración de seguridad de macOS")

    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
