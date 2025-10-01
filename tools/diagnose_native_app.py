#!/usr/bin/env python3
"""
Script de diagnóstico para la aplicación nativa macOS
Autor: EDF Developer - 2025
"""

import os
import subprocess
import time
from datetime import datetime

import requests


def check_native_app_process():
    """Verifica si la aplicación nativa está ejecutándose"""
    print("🔍 VERIFICANDO PROCESO DE LA APLICACIÓN NATIVA")
    print("=" * 50)

    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        lines = result.stdout.split("\n")

        app_processes = []
        for line in lines:
            if "EDF_CatalogoDeTablas_Web_Native" in line and "grep" not in line:
                app_processes.append(line)

        if app_processes:
            print(f"✅ Aplicación nativa ejecutándose: {len(app_processes)} proceso(s)")
            for process in app_processes:
                print(f"   - {process.strip()}")
            return True
        else:
            print("❌ Aplicación nativa no está ejecutándose")
            return False

    except Exception as e:
        print(f"❌ Error verificando proceso: {e}")
        return False


def check_network_ports():
    """Verifica los puertos de red en uso"""
    print("\n🌐 VERIFICANDO PUERTOS DE RED")
    print("=" * 50)

    try:
        # Verificar puerto 5001
        result = subprocess.run(["lsof", "-i", ":5001"], capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ Puerto 5001 en uso:")
            print(result.stdout)
            return True
        else:
            print("❌ Puerto 5001 no está en uso")

        # Verificar otros puertos comunes
        common_ports = [5000, 8000, 8080, 3000]
        for port in common_ports:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], capture_output=True, text=True
            )
            if result.stdout.strip():
                print(f"⚠️  Puerto {port} en uso:")
                print(result.stdout)

        return False

    except Exception as e:
        print(f"❌ Error verificando puertos: {e}")
        return False


def test_webview_connection():
    """Prueba la conexión a la aplicación webview"""
    print("\n🖥️  PROBANDO CONEXIÓN WEBVIEW")
    print("=" * 50)

    # Probar diferentes puertos
    ports = [5001, 5000, 8000, 8080, 3000]

    for port in ports:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            if response.status_code == 200:
                print(f"✅ Aplicación respondiendo en puerto {port}")
                return port
            else:
                print(f"⚠️  Puerto {port} responde con código: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Puerto {port} no responde")
        except Exception as e:
            print(f"❌ Error probando puerto {port}: {e}")

    print("❌ No se encontró ningún puerto respondiendo")
    return None


def check_app_logs():
    """Verifica los logs de la aplicación"""
    print("\n📋 VERIFICANDO LOGS DE LA APLICACIÓN")
    print("=" * 50)

    app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"

    # Verificar archivos de sesión
    session_dir = os.path.join(app_path, "Contents", "MacOS", "flask_session")
    if os.path.exists(session_dir):
        session_files = os.listdir(session_dir)
        print(f"✅ Archivos de sesión encontrados: {len(session_files)}")
        for file in session_files[:3]:  # Mostrar solo los primeros 3
            print(f"   - {file}")
    else:
        print("❌ Directorio de sesiones no encontrado")

    # Verificar archivos .env
    env_files = [
        os.path.join(app_path, ".env"),
        os.path.join(app_path, "Contents", "Resources", ".env"),
    ]

    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Archivo .env encontrado: {env_file}")
            # Verificar contenido (sin mostrar credenciales)
            try:
                with open(env_file, "r") as f:
                    content = f.read()
                    if "MONGO_URI=" in content:
                        print("   - MONGO_URI configurada")
                    else:
                        print("   - MONGO_URI no encontrada")
            except Exception as e:
                print(f"   - Error leyendo archivo: {e}")
        else:
            print(f"❌ Archivo .env no encontrado: {env_file}")


def check_app_permissions():
    """Verifica los permisos de la aplicación"""
    print("\n🔐 VERIFICANDO PERMISOS")
    print("=" * 50)

    app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"

    try:
        # Verificar permisos de la aplicación
        stat = os.stat(app_path)
        permissions = oct(stat.st_mode)[-3:]
        print(f"📁 Permisos de la aplicación: {permissions}")

        # Verificar permisos del ejecutable
        executable_path = os.path.join(
            app_path, "Contents", "MacOS", "EDF_CatalogoDeTablas_Web_Native"
        )
        if os.path.exists(executable_path):
            stat = os.stat(executable_path)
            permissions = oct(stat.st_mode)[-3:]
            print(f"⚙️  Permisos del ejecutable: {permissions}")

            if permissions == "755":
                print("✅ Permisos de ejecución correctos")
            else:
                print("❌ Permisos de ejecución incorrectos")
        else:
            print("❌ Ejecutable no encontrado")

    except Exception as e:
        print(f"❌ Error verificando permisos: {e}")


def restart_native_app():
    """Reinicia la aplicación nativa"""
    print("\n🔄 REINICIANDO APLICACIÓN NATIVA")
    print("=" * 50)

    try:
        # Detener aplicación si está ejecutándose
        subprocess.run(
            ["pkill", "-f", "EDF_CatalogoDeTablas_Web_Native"], capture_output=True
        )
        print("✅ Aplicación detenida")

        # Esperar un momento
        time.sleep(2)

        # Iniciar aplicación nuevamente
        app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"
        subprocess.run(["open", app_path], capture_output=True)
        print("✅ Aplicación iniciada")

        # Esperar a que se inicie
        time.sleep(5)

        return True

    except Exception as e:
        print(f"❌ Error reiniciando aplicación: {e}")
        return False


def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO APLICACIÓN NATIVA MACOS")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Paso 1: Verificar proceso
        app_running = check_native_app_process()

        # Paso 2: Verificar puertos
        ports_ok = check_network_ports()

        # Paso 3: Probar conexión webview
        working_port = test_webview_connection()

        # Paso 4: Verificar logs
        check_app_logs()

        # Paso 5: Verificar permisos
        check_app_permissions()

        # Resumen
        print("\n📊 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 50)

        if app_running:
            print("✅ Aplicación nativa está ejecutándose")
        else:
            print("❌ Aplicación nativa no está ejecutándose")

        if working_port:
            print(f"✅ Aplicación respondiendo en puerto {working_port}")
            print(f"🌐 URL: http://localhost:{working_port}")
        else:
            print("❌ Aplicación no responde en ningún puerto")

        if not app_running or not working_port:
            print("\n🔧 RECOMENDACIONES:")
            print("   1. Ejecuta: ./launch_native_app.sh")
            print("   2. O haz doble clic en: dist/EDF_CatalogoDeTablas_Web_Native.app")
            print(
                "   3. Si persiste el problema, ejecuta: python3 tools/fix_native_app_macos.py"
            )

    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
