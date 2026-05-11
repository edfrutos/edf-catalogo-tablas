# Script: admin_backup_utils.py
# Descripción: Utilidades compartidas para gestión de backups administrativos.
# Autor: EDF Developer

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_backup_dir() -> str:
    """Obtiene el directorio de backups, asegurando que exista."""
    backup_dir = os.path.abspath(os.path.join(os.getcwd(), "backups"))
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def get_backup_files(backup_dir: str) -> List[Dict[str, Any]]:
    """Obtiene la lista de archivos de backup disponibles."""
    try:
        logger.info("Buscando archivos de backup en: %s", backup_dir)

        if not os.path.exists(backup_dir):
            logger.warning("El directorio de backups no existe: %s", backup_dir)
            os.makedirs(backup_dir, exist_ok=True)
            logger.info("Directorio de backups creado: %s", backup_dir)
            return []

        backup_files: List[Dict[str, Any]] = []

        for file in os.listdir(backup_dir):
            if file.startswith("."):
                continue

            full_path = os.path.join(backup_dir, file)

            if not os.path.isfile(full_path):
                continue

            if not any(
                file.endswith(ext)
                for ext in [
                    ".bak",
                    ".backup",
                    ".zip",
                    ".tar",
                    ".gz",
                    ".json.gz",
                    ".sql",
                    ".dump",
                    ".old",
                    ".back",
                    ".tmp",
                    ".swp",
                    "~",
                    ".csv",
                    ".json",
                ]
            ):
                continue

            stats = os.stat(full_path)
            size_bytes = stats.st_size

            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

            mod_time = datetime.fromtimestamp(stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            backup_files.append(
                {
                    "name": file,
                    "size": size_str,
                    "modified": mod_time,
                    "path": full_path,
                }
            )

        backup_files.sort(key=lambda x: x["modified"], reverse=True)
        return backup_files[:20]

    except (OSError, PermissionError) as e:
        logger.error("Error al obtener archivos de backup: %s", str(e), exc_info=True)
        return []
