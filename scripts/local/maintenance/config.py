#!/usr/bin/env python3
"""
Configuración centralizada para scripts de mantenimiento.
Define rutas, configuraciones y constantes compartidas.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class MaintenanceConfig:
    """Configuración centralizada para scripts de mantenimiento."""

    # Obtener la ruta raíz del proyecto de forma robusta
    @staticmethod
    def get_project_root():
        """Obtiene la ruta raíz del proyecto."""
        current_path = Path(__file__).resolve()

        # Buscar archivos característicos del proyecto
        for parent in [current_path] + list(current_path.parents):
            if (parent / ".env").exists() or (parent / "main_app.py").exists():
                return parent

        return Path.cwd()

    # Rutas del proyecto
    PROJECT_ROOT = get_project_root()
    SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "local" / "maintenance"
    LOGS_DIR = PROJECT_ROOT / "logs"
    MAINTENANCE_LOGS_DIR = SCRIPTS_DIR / "logs"

    # Configuración de MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "app_catalogojoyero_nueva")

    # Configuración de directorios de imágenes
    UPLOAD_FOLDER = PROJECT_ROOT / "app" / "static" / "imagenes_subidas"
    UNUSED_IMAGES_FOLDER = SCRIPTS_DIR / "unused_images"

    # Configuración de logging
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Configuración de limpieza
    DEFAULT_RETENTION_DAYS = 30
    CLEANUP_MODE = os.getenv("CLEANUP_MODE", "move")  # 'move' o 'delete'

    # Configuración de correo
    SEND_EMAIL = os.getenv("SEND_EMAIL", "False").lower() == "true"
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    EMAIL_SERVER = os.getenv("EMAIL_SERVER", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

    # Configuración de backup
    BACKUP_DIR = PROJECT_ROOT / "backups"
    INCREMENTAL_STATE_FILE = BACKUP_DIR / "incremental_state.json"

    # Configuración de monitoreo
    DISK_USAGE_THRESHOLD = 80  # Porcentaje de uso de disco para alertas
    MEMORY_USAGE_THRESHOLD = 85  # Porcentaje de uso de memoria para alertas

    @classmethod
    def setup_environment(cls):
        """Configura el entorno para la ejecución de scripts."""
        # Crear directorios necesarios
        cls.MAINTENANCE_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Agregar el directorio raíz al path de Python
        if str(cls.PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(cls.PROJECT_ROOT))

        return cls.PROJECT_ROOT


# Instancia global de configuración
config = MaintenanceConfig()
