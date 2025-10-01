#!/usr/bin/env python3
"""
Script para limpiar y actualizar dependencias de manera segura.
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Ejecuta un comando y muestra su salida."""
    print(f"Ejecutando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
        print(f"Salida de error: {e.stderr}")
        return False


def main():
    # 1. Crear un entorno limpio
    print("\n=== Creando entorno virtual limpio ===")
    venv_path = ".venv_clean"
    if not os.path.exists(venv_path):
        if not run_command([sys.executable, "-m", "venv", venv_path]):
            return

    # Determinar el comando pip del entorno virtual
    pip_cmd = os.path.join(venv_path, "bin", "pip")
    if sys.platform == "win32":
        pip_cmd = os.path.join(venv_path, "Scripts", "pip.exe")

    # 2. Instalar dependencias
    print("\n=== Instalando dependencias limpias ===")
    if not run_command([pip_cmd, "install", "-r", "requirements.txt"]):
        return

    # 3. Generar requirements limpio
    print("\n=== Generando requirements limpio ===")
    with open("requirements_clean.txt", "w") as f:
        subprocess.run([pip_cmd, "freeze"], stdout=f, check=True)

    print("\n=== Proceso completado ===")
    print(
        "Se ha generado el archivo 'requirements_clean.txt' con las dependencias limpias."
    )
    print(
        "Puedes revisarlo y luego reemplazar el requirements.txt original si lo deseas."
    )


if __name__ == "__main__":
    main()
