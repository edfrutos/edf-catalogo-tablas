# Script: temp_files_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 temp_files_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import os
import time  # noqa: F401
import tempfile
import platform
from datetime import datetime
from typing import List, Dict, Optional, Union


def list_temp_files(prefix: str = "edefrutos2025_", directory: Optional[str] = None) -> List[Dict[str, Union[str, float]]]:
    """
    Devuelve una lista de archivos temporales con detalles (nombre, tamaño MB, fecha modificación).
    Busca en múltiples ubicaciones según el sistema operativo.
    """
    files: List[Dict[str, Union[str, float]]] = []

    # Determinar directorios a buscar según el SO
    temp_dirs: List[str] = []
    if directory:
        temp_dirs.append(directory)
    else:
        # Directorio temporal del sistema
        temp_dirs.append(tempfile.gettempdir())

        # Directorios adicionales según el SO
        if platform.system() == "Darwin":  # macOS
            temp_dirs.extend(
                [
                    "/var/folders/*/*/T",  # Temp folders de macOS
                    f"{os.path.expanduser('~')}/Library/Caches/TemporaryItems",
                ]
            )
        elif platform.system() == "Linux":
            temp_dirs.extend(["/tmp", "/var/tmp"])
        elif platform.system() == "Windows":
            temp_dirs.extend([os.environ.get("TEMP", ""), os.environ.get("TMP", "")])

    # Buscar archivos en cada directorio
    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir):
            continue

        try:
            # Manejar wildcards en la ruta (para macOS)
            if "*" in temp_dir:
                import glob

                expanded_dirs = glob.glob(temp_dir)
                for expanded_dir in expanded_dirs:
                    files.extend(_scan_directory(expanded_dir, prefix))
            else:
                files.extend(_scan_directory(temp_dir, prefix))
        except (PermissionError, OSError):
            continue  # Ignorar directorios sin permisos

    # Eliminar duplicados y ordenar
    seen: set[str] = set()
    unique_files: List[Dict[str, Union[str, float]]] = []
    for file in files:
        if file["name"] not in seen:
            seen.add(file["name"])
            unique_files.append(file)

    unique_files.sort(key=lambda x: x["mtime"], reverse=True)
    return unique_files


def _scan_directory(directory: str, prefix: str) -> List[Dict[str, Union[str, float]]]:
    """Escanea un directorio específico buscando archivos con el prefijo dado."""
    files: List[Dict[str, Union[str, float]]] = []
    try:
        for file in os.listdir(directory):
            if file.startswith(prefix):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    try:
                        stats = os.stat(file_path)
                        size_mb = round(stats.st_size / (1024 * 1024), 2)
                        mtime = datetime.fromtimestamp(stats.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        files.append(
                            {
                                "name": file,
                                "size_mb": size_mb,
                                "mtime": mtime,
                                "path": directory,
                            }
                        )
                    except (PermissionError, OSError):
                        continue
    except (PermissionError, OSError):
        pass
    return files


def delete_temp_files(filenames: List[str], prefix: str = "edefrutos2025_", directory: Optional[str] = None) -> int:
    """
    Elimina archivos temporales seleccionados por nombre.
    Busca en múltiples ubicaciones si no se especifica directorio.
    """
    removed = 0

    # Obtener lista actual de archivos temporales con sus rutas
    current_files = list_temp_files(prefix, directory)
    file_paths: Dict[str, str] = {f["name"]: f["path"] for f in current_files}

    for filename in filenames:
        if filename.startswith(prefix) and filename in file_paths:
            file_path = os.path.join(file_paths[filename], filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    removed += 1
                except (PermissionError, OSError):
                    continue
    return removed
