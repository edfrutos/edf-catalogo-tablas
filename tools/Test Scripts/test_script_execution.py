#!/usr/bin/env python3

# Script: test_script_execution.py
# Descripción: [Script para probar la ejecución de scripts desde la interfaz web]
# Uso: python3 test_script_execution.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [EDF Developer] - 2025-06-05

import json
import os
import subprocess
import sys

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")


def print_header(message):
    print("\n" + "=" * 80)
    print(f"{message}".center(80))
    print("=" * 80)


def test_script_execution():
    """Prueba la ejecución de algunos scripts desde la interfaz web"""
    print("Probando la ejecución de scripts...")

    # Lista de scripts a probar
    test_scripts = [
        "test_script.sh",
        "supervise_gunicorn_web.sh",
        "check_logs.py",
        "check_mongodb_simple.py",
    ]

    # Probar cada script
    success_count = 0
    for script in test_scripts:
        print(f"  Probando script: {script}")

        # Buscar el script
        script_found = False
        script_path = None

        # Buscar en el directorio raíz (enlaces simbólicos)
        root_path = os.path.join(TOOLS_DIR, script)
        if os.path.exists(root_path):
            script_found = True
            script_path = root_path

        # Si no se encuentra, buscar en subdirectorios
        if not script_found:
            for root, dirs, files in os.walk(TOOLS_DIR):
                if script in files:
                    script_found = True
                    script_path = os.path.join(root, script)
                    break

        if not script_found:
            print(f"    ❌ Script no encontrado: {script}")
            continue

        # Probar la ejecución del script
        try:
            # Usar script_runner.py para ejecutar el script
            runner_path = os.path.join(TOOLS_DIR, "script_runner.py")
            if not os.path.exists(runner_path):
                print(f"    ❌ script_runner.py no encontrado")  # noqa: F541
                continue

            result = subprocess.run(
                [sys.executable, runner_path, script_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Verificar el resultado
            try:
                result_json = json.loads(result.stdout)
                exit_code = result_json.get("exit_code")

                if exit_code == 0:
                    print(f"    ✅ Script ejecutado correctamente")  # noqa: F541
                    success_count += 1
                else:
                    print(f"    ⚠️ Script ejecutado con errores (código {exit_code})")
                    print(f"    - Error: {result_json.get('error', '')}")
            except Exception as e:
                print(f"    ❌ Error al analizar la salida: {str(e)}")
                print(f"    - Salida: {result.stdout[:100]}...")

        except Exception as e:
            print(f"    ❌ Error al ejecutar el script: {str(e)}")

    print(f"Se ejecutaron correctamente {success_count} de {len(test_scripts)} scripts")
    return success_count == len(test_scripts)


def restart_service():
    """Reinicia el servicio edefrutos2025"""
    print("Reiniciando el servicio edefrutos2025...")

    try:
        result = subprocess.run(
            ["systemctl", "restart", "edefrutos2025"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Servicio reiniciado correctamente")

            # Verificar el estado del servicio
            status_result = subprocess.run(
                ["systemctl", "status", "edefrutos2025"], capture_output=True, text=True
            )
            if "Active: active (running)" in status_result.stdout:
                print("✅ El servicio está activo y en ejecución")
                return True
            else:
                print(f"❌ El servicio no está en ejecución: {status_result.stdout}")
                return False
        else:
            print(f"❌ Error al reiniciar el servicio: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error al reiniciar el servicio: {str(e)}")
        return False


def main():
    print_header("PRUEBA DE EJECUCIÓN DE SCRIPTS")

    # Reiniciar el servicio
    print_header("REINICIANDO EL SERVICIO")
    service_restarted = restart_service()

    # Probar la ejecución de scripts
    print_header("PROBANDO LA EJECUCIÓN DE SCRIPTS")
    scripts_executable = test_script_execution()

    print_header("RESULTADOS")
    print(
        f"1. {'✅' if service_restarted else '❌'} El servicio edefrutos2025 se reinició {'correctamente' if service_restarted else 'con errores'}"
    )
    print(
        f"2. {'✅' if scripts_executable else '❌'} Los scripts son {'accesibles y ejecutables' if scripts_executable else 'no accesibles o ejecutables'}"
    )

    if not service_restarted or not scripts_executable:
        print("\n⚠️ Se encontraron problemas que requieren atención:")
        if not service_restarted:
            print("  - El servicio edefrutos2025 no se reinició correctamente")
        if not scripts_executable:
            print("  - Algunos scripts no son accesibles o ejecutables")
    else:
        print(
            "\n✅ Todo funciona correctamente. Los scripts están organizados y son accesibles y ejecutables."
        )


if __name__ == "__main__":
    main()
