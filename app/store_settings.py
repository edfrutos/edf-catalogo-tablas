"""Ajustes de la edición de tienda: perfil del propietario y carpeta local de copias.

Todo se guarda en el almacén local (colección ``app_settings``). En el sandbox de macOS una
carpeta elegida por el usuario solo es accesible mientras la app está abierta; para recordarla
entre arranques se guarda un *security-scoped bookmark* (requiere el entitlement
``com.apple.security.files.bookmarks.app-scope``). Sin PyObjC (desarrollo en Linux) se guarda
solo la ruta.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import uuid
from typing import Any

logger = logging.getLogger(__name__)

COLECCION = "app_settings"
DOC_ID = "store"
MAX_NOMBRE = 100
MAX_ORGANIZACION = 120
MAX_EMAIL = 254
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_abiertos: dict[str, str] = {}  # marcador -> ruta ya abierta en esta sesión


# ------------------------------------------------------------------ perfil y carpeta
def cargar(db) -> dict[str, Any]:
    doc = db[COLECCION].find_one({"_id": DOC_ID}) or {}
    return {
        "nombre": doc.get("nombre", ""),
        "email": doc.get("email", ""),
        "organizacion": doc.get("organizacion", ""),
        "carpeta": doc.get("carpeta", ""),
        "marcador": doc.get("marcador", ""),
    }


def validar_perfil(form) -> tuple[dict[str, str], list[str]]:
    nombre = (form.get("nombre") or "").strip()
    email = (form.get("email") or "").strip()
    organizacion = (form.get("organizacion") or "").strip()
    errores: list[str] = []
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if len(nombre) > MAX_NOMBRE:
        errores.append(f"El nombre admite como máximo {MAX_NOMBRE} caracteres.")
    if email and (len(email) > MAX_EMAIL or not _EMAIL.match(email)):
        errores.append("El correo no tiene un formato válido.")
    if len(organizacion) > MAX_ORGANIZACION:
        errores.append(f"La organización admite como máximo {MAX_ORGANIZACION} caracteres.")
    return {"nombre": nombre, "email": email, "organizacion": organizacion}, errores


def _guardar(db, campos: dict[str, Any]) -> None:
    db[COLECCION].update_one({"_id": DOC_ID}, {"$set": campos}, upsert=True)


def guardar_perfil(db, perfil: dict[str, str]) -> None:
    _guardar(db, perfil)


def guardar_carpeta(db, carpeta: str, marcador: str = "") -> None:
    _guardar(db, {"carpeta": carpeta, "marcador": marcador})


def olvidar_carpeta(db) -> None:
    _guardar(db, {"carpeta": "", "marcador": ""})


# ------------------------------------------------------------------ carpeta y marcadores
def es_escribible(carpeta: str) -> bool:
    """True si se puede crear (y borrar) un archivo en la carpeta: prueba real del acceso."""
    if not carpeta or not os.path.isabs(carpeta) or not os.path.isdir(carpeta):
        return False
    prueba = os.path.join(carpeta, f".tablateca_{uuid.uuid4().hex}")
    try:
        with open(prueba, "wb") as f:
            f.write(b"")
        os.remove(prueba)
        return True
    except OSError:
        return False


def crear_marcador(ruta: str) -> str:
    """Marcador de seguridad (base64) de una carpeta; "" si no está disponible (p. ej. sin PyObjC)."""
    try:
        from Foundation import NSURL, NSURLBookmarkCreationWithSecurityScope
    except Exception:  # noqa: BLE001 - fuera de macOS no existe
        return ""
    try:
        url = NSURL.fileURLWithPath_isDirectory_(ruta, True)
        datos, error = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(
            NSURLBookmarkCreationWithSecurityScope, None, None, None
        )
        if datos is None:
            logger.warning("No se pudo crear el marcador de %s: %s", ruta, error)
            return ""
        return base64.b64encode(bytes(datos)).decode("ascii")
    except Exception:  # noqa: BLE001
        logger.exception("Error al crear el marcador de seguridad")
        return ""


def abrir_marcador(marcador: str) -> str:
    """Resuelve el marcador y abre el acceso a la carpeta en esta sesión; devuelve su ruta o ""."""
    if not marcador:
        return ""
    if marcador in _abiertos:
        return _abiertos[marcador]
    try:
        from Foundation import NSURL, NSData, NSURLBookmarkResolutionWithSecurityScope
    except Exception:  # noqa: BLE001
        return ""
    try:
        crudo = base64.b64decode(marcador)
        datos = NSData.dataWithBytes_length_(crudo, len(crudo))
        url, _obsoleto, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
            datos, NSURLBookmarkResolutionWithSecurityScope, None, None, None
        )
        if url is None:
            logger.warning("No se pudo resolver el marcador: %s", error)
            return ""
        url.startAccessingSecurityScopedResource()
        ruta = str(url.path())
        _abiertos[marcador] = ruta
        return ruta
    except Exception:  # noqa: BLE001
        logger.exception("Error al abrir el marcador de seguridad")
        return ""


def carpeta_de_copias(ajustes: dict[str, Any]) -> str:
    """Carpeta de copias utilizable ahora mismo, o "" si no hay o ya no es accesible."""
    candidata = abrir_marcador(ajustes.get("marcador", "")) or ajustes.get("carpeta", "")
    return candidata if es_escribible(candidata) else ""


def preparar_carpeta(ruta: str) -> dict[str, str]:
    """Lo que devuelve el diálogo nativo a la página: la ruta y su marcador de seguridad."""
    return {"carpeta": ruta, "marcador": crear_marcador(ruta)}
