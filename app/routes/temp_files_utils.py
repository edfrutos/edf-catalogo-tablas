import os
import time
from datetime import datetime

def list_temp_files(prefix="edefrutos2025_", directory="/tmp/"):
    """
    Devuelve una lista de archivos temporales con detalles (nombre, tamaño MB, fecha modificación).
    """
    files = []
    for file in os.listdir(directory):
        if file.startswith(prefix):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                size_mb = round(stats.st_size / (1024 * 1024), 2)
                mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                files.append({
                    'name': file,
                    'size_mb': size_mb,
                    'mtime': mtime
                })
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files

def delete_temp_files(filenames, prefix="edefrutos2025_", directory="/tmp/"):
    """
    Elimina archivos temporales seleccionados por nombre.
    """
    removed = 0
    for file in filenames:
        if file.startswith(prefix):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    removed += 1
                except Exception:
                    pass
    return removed
