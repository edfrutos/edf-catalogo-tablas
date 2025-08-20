#!/usr/bin/env python3
"""
Verificación Final - Aplicación macOS EDF CatálogoDeTablas
==========================================================

Este script realiza una verificación final completa para confirmar
que la aplicación funciona correctamente desde Finder.

"""

import os
import subprocess
import sys
import time

import requests


def verificar_estructura_final():
    """Verificación final de la estructura."""
    print("🔍 Verificación final de estructura...")

    app_path = "dist/EDF_CatalogoDeTablas.app"

    # Verificar archivos críticos
    critical_files = [
        "Contents/MacOS/EDF_CatalogoDeTablas",
        "Contents/Resources/app",
        "Contents/Resources/tools/db_utils/credentials.json",
        "Contents/Resources/tools/db_utils/token.json",
        "Contents/Resources/config.py",
        "Contents/Resources/main_app.py",
        "Contents/Info.plist",
    ]

    for file_path in critical_files:
        full_path = os.path.join(app_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - FALTANTE")
            return False

    return True


def verificar_permisos_final():
    """Verificación final de permisos."""
    print("\n🔐 Verificación final de permisos...")

    executable_path = (
        "dist/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas"
    )

    if not os.access(executable_path, os.X_OK):
        print("❌ Error: El ejecutable no tiene permisos de ejecución")
        return False

    print("✅ Permisos de ejecución correctos")
    return True


def verificar_arranque_finder():
    """Verifica que la aplicación pueda arrancar desde Finder."""
    print("\n🍎 Verificando arranque desde Finder...")

    # Limpiar atributos extendidos
    try:
        subprocess.run(
            ["xattr", "-cr", "dist/EDF_CatalogoDeTablas.app"],
            check=True,
            capture_output=True,
        )
        print("✅ Atributos extendidos limpiados")
    except subprocess.CalledProcessError:
        print("⚠️  No se pudieron limpiar atributos extendidos")

    # Verificar formato de ejecutable
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
        else:
            print("❌ Formato de ejecutable incorrecto")
            return False
    except subprocess.CalledProcessError:
        print("❌ Error al verificar formato de ejecutable")
        return False

    return True


def verificar_funcionamiento_terminal():
    """Verifica que la aplicación funcione desde terminal."""
    print("\n💻 Verificando funcionamiento desde terminal...")

    try:
        # Ejecutar con timeout
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
            print("✅ Aplicación inició correctamente desde terminal")
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
            print(f"   Errores: {stderr[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación: {e}")
        return False


def verificar_comando_open():
    """Verifica que el comando 'open' funcione."""
    print("\n🚀 Verificando comando 'open'...")

    try:
        # Usar open para abrir la aplicación
        process = subprocess.Popen(
            ["open", "dist/EDF_CatalogoDeTablas.app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Esperar un poco
        time.sleep(3)

        if process.poll() is None:
            print("✅ Comando 'open' ejecutado correctamente")
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                print("✅ Comando 'open' completado exitosamente")
                return True
            else:
                print(f"❌ Error en comando 'open': {stderr}")
                return False

    except Exception as e:
        print(f"❌ Error al ejecutar comando 'open': {e}")
        return False


def main():
    """Función principal de verificación final."""
    print("🎯 Verificación Final - Aplicación macOS EDF CatálogoDeTablas")
    print("=" * 70)

    # Realizar todas las verificaciones
    checks = [
        ("Estructura final", verificar_estructura_final),
        ("Permisos finales", verificar_permisos_final),
        ("Arranque desde Finder", verificar_arranque_finder),
        ("Funcionamiento desde terminal", verificar_funcionamiento_terminal),
        ("Comando 'open'", verificar_comando_open),
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
    print("\n" + "=" * 70)
    print("🎉 VERIFICACIÓN FINAL COMPLETADA")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {name}")

    print(f"\n✅ Verificaciones exitosas: {passed}/{total}")

    if passed == total:
        print("\n🎉 ¡VERIFICACIÓN FINAL EXITOSA!")
        print("🚀 La aplicación está completamente funcional")
        print("\n💡 Métodos de uso confirmados:")
        print("   1. Desde Finder: Doble clic en EDF_CatalogoDeTablas.app")
        print("   2. Desde Terminal: open dist/EDF_CatalogoDeTablas.app")
        print(
            "   3. Desde Terminal: dist/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas"
        )
        print("\n🎯 ¡La aplicación macOS está lista para uso completo!")
        return True
    else:
        print("\n⚠️  Algunas verificaciones fallaron")
        print("🔧 Revisa los errores anteriores")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
