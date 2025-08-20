#!/usr/bin/env python3
"""
Diagnóstico de la Aplicación macOS EDF CatálogoDeTablas
=======================================================

Este script verifica que todos los componentes de la aplicación
estén funcionando correctamente.

"""

import json
import os
import subprocess
import sys
import time

import requests


def verificar_estructura_app():
    """Verifica la estructura de la aplicación."""
    print("🔍 Verificando estructura de la aplicación...")

    app_path = "dist/EDF_CatalogoDeTablas.app"

    if not os.path.exists(app_path):
        print("❌ Error: No se encontró la aplicación")
        return False

    # Verificar archivos críticos
    critical_files = [
        "Contents/MacOS/EDF_CatalogoDeTablas",
        "Contents/Resources/app",
        "Contents/Resources/tools/db_utils/credentials.json",
        "Contents/Resources/tools/db_utils/token.json",
        "Contents/Resources/config.py",
        "Contents/Resources/main_app.py",
    ]

    for file_path in critical_files:
        full_path = os.path.join(app_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - FALTANTE")
            return False

    return True


def verificar_permisos():
    """Verifica los permisos de ejecución."""
    print("\n🔐 Verificando permisos...")

    executable_path = (
        "dist/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas"
    )

    if not os.access(executable_path, os.X_OK):
        print("❌ Error: El ejecutable no tiene permisos de ejecución")
        return False

    print("✅ Permisos de ejecución correctos")
    return True


def verificar_credenciales():
    """Verifica que las credenciales de Google Drive estén presentes."""
    print("\n🔑 Verificando credenciales...")

    creds_path = "dist/EDF_CatalogoDeTablas.app/Contents/Resources/tools/db_utils/credentials.json"
    token_path = (
        "dist/EDF_CatalogoDeTablas.app/Contents/Resources/tools/db_utils/token.json"
    )

    if not os.path.exists(creds_path):
        print("❌ Error: credentials.json no encontrado")
        return False

    if not os.path.exists(token_path):
        print("❌ Error: token.json no encontrado")
        return False

    # Verificar que los archivos no estén vacíos
    if os.path.getsize(creds_path) < 100:
        print("❌ Error: credentials.json parece estar vacío")
        return False

    if os.path.getsize(token_path) < 100:
        print("❌ Error: token.json parece estar vacío")
        return False

    print("✅ Credenciales de Google Drive presentes")
    return True


def verificar_arranque_finder():
    """Verifica que la aplicación pueda arrancar desde Finder."""
    print("\n🍎 Verificando arranque desde Finder...")

    # Limpiar atributos extendidos que puedan bloquear la ejecución
    try:
        subprocess.run(
            ["xattr", "-cr", "dist/EDF_CatalogoDeTablas.app"],
            check=True,
            capture_output=True,
        )
        print("✅ Atributos extendidos limpiados")
    except subprocess.CalledProcessError:
        print("⚠️  No se pudieron limpiar atributos extendidos")

    # Verificar que la aplicación tenga el formato correcto
    try:
        result = subprocess.run(
            [
                "file",
                "dist/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        if "Mach-O" in result.stdout:
            print("✅ Formato de ejecutable correcto (Mach-O)")
            return True
        else:
            print("❌ Formato de ejecutable incorrecto")
            return False
    except subprocess.CalledProcessError:
        print("❌ Error al verificar formato de ejecutable")
        return False


def verificar_funcionamiento_basico():
    """Verifica el funcionamiento básico de la aplicación."""
    print("\n🚀 Verificando funcionamiento básico...")

    # Intentar ejecutar la aplicación en modo prueba
    try:
        # Ejecutar con timeout para evitar que se quede colgada
        process = subprocess.Popen(
            ["dist/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Esperar un poco para que inicie
        time.sleep(5)

        # Verificar si el proceso sigue ejecutándose
        if process.poll() is None:
            print("✅ Aplicación inició correctamente")
            # Terminar el proceso
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ La aplicación se cerró prematuramente")
            print(f"   Salida: {stdout[:200]}...")
            print(f"   Errores: {stderr[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación: {e}")
        return False


def verificar_conectividad():
    """Verifica la conectividad de red."""
    print("\n🌐 Verificando conectividad...")

    try:
        # Verificar conexión a internet
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("✅ Conexión a internet funcionando")
        else:
            print("⚠️  Conexión a internet limitada")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False

    return True


def main():
    """Función principal de diagnóstico."""
    print("🔧 Diagnóstico de la Aplicación macOS EDF CatálogoDeTablas")
    print("=" * 60)

    # Realizar todas las verificaciones
    checks = [
        ("Estructura de la aplicación", verificar_estructura_app),
        ("Permisos de ejecución", verificar_permisos),
        ("Credenciales de Google Drive", verificar_credenciales),
        ("Arranque desde Finder", verificar_arranque_finder),
        ("Conectividad de red", verificar_conectividad),
    ]

    results = []
    for name, check_func in checks:
        try:
            print(f"\n📋 {name}:")
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {name}")

    print(f"\n✅ Verificaciones exitosas: {passed}/{total}")

    if passed == total:
        print("🎉 ¡Todas las verificaciones pasaron!")
        print("🚀 La aplicación está lista para uso completo")
        print("\n💡 Para usar la aplicación:")
        print("   1. Abre Finder")
        print("   2. Navega a la carpeta dist/")
        print("   3. Haz doble clic en EDF_CatalogoDeTablas.app")
        return True
    else:
        print("⚠️  Algunas verificaciones fallaron")
        print("🔧 Revisa los errores anteriores")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
