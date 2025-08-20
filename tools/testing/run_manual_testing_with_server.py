#!/usr/bin/env python3
"""
Script para ejecutar testing manual con servidor en paralelo
"""

import os
import subprocess
import sys
import time

import requests


def start_server():
    """Inicia el servidor Flask"""
    print("🚀 Iniciando servidor Flask...")

    # Activar entorno virtual y iniciar servidor
    cmd = [
        "source",
        ".venv/bin/activate",
        "&&",
        ".venv/bin/python",
        "-m",
        "flask",
        "run",
        "--debug",
        "--port=5001",
        "--host=0.0.0.0",
    ]

    # Iniciar servidor en background
    process = subprocess.Popen(
        " ".join(cmd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    return process


def wait_for_server(max_wait=30):
    """Espera a que el servidor esté listo"""
    print("⏳ Esperando a que el servidor esté listo...")

    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:5001", timeout=2)
            if response.status_code == 200:
                print("✅ Servidor listo!")
                return True
        except:
            pass

        print(f"   Esperando... ({i+1}/{max_wait})")
        time.sleep(1)

    print("❌ Servidor no respondió en el tiempo esperado")
    return False


def run_manual_testing():
    """Ejecuta el testing manual"""
    print("🧪 Ejecutando testing manual...")

    try:
        result = subprocess.run(
            ["python", "tools/testing/testing_manual_exhaustivo.py"],
            capture_output=True,
            text=True,
        )

        print("📋 Resultado del testing manual:")
        print(result.stdout)

        if result.stderr:
            print("⚠️ Errores:")
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error ejecutando testing manual: {e}")
        return False


def main():
    """Función principal"""
    print("🧪 Testing Manual con Servidor - EDF CatálogoDeTablas")
    print("=" * 60)

    # Iniciar servidor
    server_process = start_server()

    try:
        # Esperar a que el servidor esté listo
        if not wait_for_server():
            print("❌ No se pudo iniciar el servidor")
            return 1

        # Ejecutar testing manual
        success = run_manual_testing()

        if success:
            print("🎉 Testing manual completado exitosamente")
            return 0
        else:
            print("❌ Testing manual falló")
            return 1

    finally:
        # Terminar servidor
        print("🛑 Terminando servidor...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    sys.exit(main())
