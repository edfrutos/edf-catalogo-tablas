"""Rutas escribibles de la aplicación.

La app macOS empaquetada (PyInstaller) va firmada y notarizada: cualquier fichero
creado dentro del .app rompe el sello ("a sealed resource is missing or invalid").
Por eso, en modo empaquetado, todo lo escribible vive en la carpeta de datos del usuario.
En desarrollo (sin empaquetar) el comportamiento es el de siempre.
"""

import os
import sys


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def user_data_dir() -> str:
    """Carpeta de datos del usuario (se crea si no existe)."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        path = os.path.join(home, "Library", "Application Support", "EDF_Catalogo")
    else:
        path = os.path.join(home, ".edf_catalogo")
    os.makedirs(path, exist_ok=True)
    return path


def writable_dir(default_root: str, name: str) -> str:
    """Devuelve la carpeta `name`.

    Empaquetada: <datos del usuario>/<name> (se crea). Desarrollo: <default_root>/<name>.
    """
    if is_frozen():
        path = os.path.join(user_data_dir(), name)
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.join(default_root, name)


def writable_uploads(default: str) -> str:
    """Carpeta de subidas: empaquetada -> <datos del usuario>/uploads; desarrollo -> `default`."""
    if is_frozen():
        return writable_dir("", "uploads")
    return default


def logs_dir(default: str) -> str:
    """Carpeta de logs: empaquetada -> $LOG_DIR o ~/Library/Logs/EDF_Catalogo; desarrollo -> `default`.

    El launcher fija LOG_DIR antes de arrancar Flask; este valor evita que las páginas de
    administración lean (o creen) una carpeta `logs` dentro del .app firmado.
    """
    if not is_frozen():
        return default
    path = os.environ.get("LOG_DIR")
    if not path:
        if sys.platform == "darwin":
            path = os.path.join(os.path.expanduser("~"), "Library", "Logs", "EDF_Catalogo")
        else:
            path = os.path.join(user_data_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path
