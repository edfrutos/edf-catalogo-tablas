"""Comprobación de nuevas versiones publicadas en GitHub Releases.

No instala nada automáticamente: solo compara la versión empaquetada (archivo
VERSION en la raíz del proyecto) contra el último release publicado en
GitHub y expone el resultado para que la interfaz muestre un aviso.
"""

import logging
import os
import re
import sys
import threading
import time

import requests

logger = logging.getLogger(__name__)

GITHUB_REPO = "edfrutos/edf-catalogo-tablas"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_TTL_SECONDS = 3600
REQUEST_TIMEOUT_SECONDS = 3

_cache_lock = threading.Lock()
_cache = {"checked_at": 0, "result": None}


def _project_root():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_current_version():
    version_file = os.path.join(_project_root(), "VERSION")
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        logger.warning("No se pudo leer VERSION en %s", version_file)
        return "0.0.0"


def _parse_version(raw):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", raw or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def check_for_update():
    """Devuelve el estado de actualización, usando una caché en memoria de 1h."""
    with _cache_lock:
        if _cache["result"] is not None and (time.time() - _cache["checked_at"]) < CACHE_TTL_SECONDS:
            return _cache["result"]

    current_version = get_current_version()
    result = {
        "current_version": current_version,
        "latest_version": None,
        "update_available": False,
        "release_url": None,
    }

    try:
        response = requests.get(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        latest_tag = data.get("tag_name", "")
        current_parsed = _parse_version(current_version)
        latest_parsed = _parse_version(latest_tag)

        result["latest_version"] = latest_tag
        result["release_url"] = data.get("html_url")
        if current_parsed and latest_parsed and latest_parsed > current_parsed:
            result["update_available"] = True
    except requests.RequestException as exc:
        logger.info("No se pudo comprobar actualizaciones (sin red o GitHub no disponible): %s", exc)
    except (ValueError, KeyError) as exc:
        logger.warning("Respuesta inesperada de la API de releases de GitHub: %s", exc)

    with _cache_lock:
        _cache["checked_at"] = time.time()
        _cache["result"] = result

    return result
