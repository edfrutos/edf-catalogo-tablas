#!/usr/bin/env python3
"""
Script wrapper para ejecutar tareas de mantenimiento desde cualquier directorio.
Maneja automáticamente las rutas y la configuración del entorno.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def get_project_root():
    """Obtiene la ruta raíz del proyecto de forma robusta."""
    # Buscar el archivo .env o config.py para identificar la raíz del proyecto
    current_path = Path(__file__).resolve()

    # Subir directorios hasta encontrar archivos característicos del proyecto
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".env").exists() or (parent / "config.py").exists():
            return parent

    # Fallback: usar el directorio actual
    return Path.cwd()


def setup_environment():
    """Configura el entorno para la ejecución de scripts."""
    project_root = get_project_root()

    # Cambiar al directorio raíz del proyecto
    os.chdir(project_root)

    # Cargar variables de entorno
    load_dotenv()

    # Agregar el directorio raíz al path de Python
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    return project_root


def run_maintenance_script(script_name, *args):
    """Ejecuta un script de mantenimiento específico."""
    project_root = setup_environment()
    script_path = project_root / "scripts" / "local" / "maintenance" / script_name

    if not script_path.exists():
        print(f"❌ Error: No se encontró el script {script_name}")
        return False

    # Construir el comando
    cmd = [sys.executable, str(script_path)] + list(args)

    try:
        print(f"🚀 Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando {script_name}: {e}")
        print(f"Salida de error: {e.stderr}")
        return False


def main():
    """Función principal del wrapper."""
    if len(sys.argv) < 2:
        print("Uso: python maintenance_wrapper.py <script_name> [argumentos...]")
        print("\nScripts disponibles:")
        print("  run_maintenance.py - Script principal de mantenimiento")
        print("  clean_images_scheduled.py - Limpieza de imágenes")
        print("  10_backup_incremental.py - Backup incremental")
        print("  clean_old_logs.py - Limpieza de logs")
        sys.exit(1)

    script_name = sys.argv[1]
    args = sys.argv[2:]

    success = run_maintenance_script(script_name, *args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
