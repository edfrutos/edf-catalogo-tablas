"""Copia de seguridad completa en ZIP para la edición de tienda.

Contenido del ZIP::

    manifest.json     app, versión del formato, fecha y recuentos
    catalogos.json    todos los catálogos (Extended JSON: conserva ObjectId y fechas)
    uploads/<nombre>  imágenes, documentos y multimedia subidos

La importación **sustituye** los catálogos actuales por los del archivo. Antes de tocar nada
se valida el ZIP entero y se guarda una copia automática del estado actual; si la sustitución
falla a medias, se restauran los catálogos anteriores.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import shutil
import tempfile
import zipfile
from typing import Any, BinaryIO

from bson import json_util
from bson.json_util import JSONMode, JSONOptions

logger = logging.getLogger(__name__)

APP_ID = "TablaTeca"
FORMATO = 1
COLECCION = "spreadsheets"
CARPETA_ARCHIVOS = "uploads/"
MAX_ARCHIVOS = 100_000
MAX_BYTES_TOTAL = 8 * 1024**3  # 8 GiB descomprimidos
MAX_BYTES_CATALOGOS = 256 * 1024**2
_OPCIONES = JSONOptions(json_mode=JSONMode.RELAXED, tz_aware=False)
# Campos de propietario: en otro Mac el usuario local tiene otro _id
_CAMPOS_PROPIETARIO = ("owner", "created_by", "owner_name", "email")


class ZipInvalido(ValueError):
    """El archivo no es una copia válida de TablaTeca (el mensaje se muestra al usuario)."""


def _archivos_de(carpeta: str) -> list[str]:
    if not os.path.isdir(carpeta):
        return []
    return sorted(
        n
        for n in os.listdir(carpeta)
        if not n.startswith(".") and os.path.isfile(os.path.join(carpeta, n))
    )


def crear_zip(db, carpeta_uploads: str, destino: BinaryIO) -> dict[str, int]:
    """Escribe la copia completa en ``destino`` (fichero abierto en binario)."""
    catalogos = list(db[COLECCION].find())
    nombres = _archivos_de(carpeta_uploads)
    manifest = {
        "app": APP_ID,
        "formato": FORMATO,
        "creado": _dt.datetime.utcnow().isoformat() + "Z",
        "catalogos": len(catalogos),
        "archivos": len(nombres),
    }
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        z.writestr(
            "catalogos.json",
            json_util.dumps(catalogos, json_options=_OPCIONES, indent=1, ensure_ascii=False),
        )
        for nombre in nombres:
            z.write(os.path.join(carpeta_uploads, nombre), CARPETA_ARCHIVOS + nombre)
    return {"catalogos": len(catalogos), "archivos": len(nombres)}


def _nombre_seguro(nombre_zip: str) -> str | None:
    """Nombre de archivo plano bajo uploads/, o None si no es un archivo de datos."""
    if not nombre_zip.startswith(CARPETA_ARCHIVOS):
        return None
    nombre = nombre_zip[len(CARPETA_ARCHIVOS):]
    if (
        not nombre
        or nombre.startswith(".")
        or "/" in nombre
        or "\\" in nombre
        or "\x00" in nombre
        or nombre in (".", "..")
        or os.path.basename(nombre) != nombre
    ):
        raise ZipInvalido(f"Nombre de archivo no permitido en la copia: {nombre_zip!r}")
    return nombre


def validar_zip(z: zipfile.ZipFile) -> tuple[dict, list[dict], list[str]]:
    """Valida el ZIP completo sin extraer nada. Devuelve (manifest, catálogos, nombres)."""
    infos = z.infolist()
    if len(infos) > MAX_ARCHIVOS:
        raise ZipInvalido("La copia contiene demasiados archivos.")
    por_nombre = {i.filename: i for i in infos}
    try:
        manifest = json.loads(z.read("manifest.json"))
    except (KeyError, ValueError):
        raise ZipInvalido("No es una copia de TablaTeca (falta el manifiesto).") from None
    if not isinstance(manifest, dict) or manifest.get("app") != APP_ID:
        raise ZipInvalido("No es una copia de TablaTeca.")
    if manifest.get("formato") != FORMATO:
        raise ZipInvalido("Esta copia procede de una versión incompatible de TablaTeca.")

    info_cat = por_nombre.get("catalogos.json")
    if info_cat is None:
        raise ZipInvalido("La copia no contiene catálogos.")
    if info_cat.file_size > MAX_BYTES_CATALOGOS:
        raise ZipInvalido("El listado de catálogos es demasiado grande.")
    try:
        catalogos = json_util.loads(z.read("catalogos.json"), json_options=_OPCIONES)
    except ValueError:
        raise ZipInvalido("El listado de catálogos está dañado.") from None
    if not isinstance(catalogos, list) or not all(isinstance(c, dict) for c in catalogos):
        raise ZipInvalido("El listado de catálogos no tiene el formato esperado.")

    nombres: list[str] = []
    total = 0
    for info in infos:
        if info.filename in ("manifest.json", "catalogos.json") or info.is_dir():
            continue
        nombre = _nombre_seguro(info.filename)
        if nombre is None:
            raise ZipInvalido(f"Contenido inesperado en la copia: {info.filename!r}")
        total += info.file_size
        if total > MAX_BYTES_TOTAL:
            raise ZipInvalido("La copia es demasiado grande.")
        nombres.append(nombre)
    if len(set(nombres)) != len(nombres):
        raise ZipInvalido("La copia contiene archivos duplicados.")
    bad = z.testzip()
    if bad is not None:
        raise ZipInvalido(f"El archivo está dañado ({bad}).")
    return manifest, catalogos, nombres


def _asignar_propietario(doc: dict, usuario: dict) -> None:
    doc["email"] = usuario.get("email", "")
    doc["created_by"] = usuario.get("username", "")
    doc["owner"] = usuario.get("username", "")
    doc["owner_name"] = usuario.get("nombre", "")
    if "created_by_id" in doc:
        doc["created_by_id"] = str(usuario["_id"])


def importar_zip(
    db,
    carpeta_uploads: str,
    origen: BinaryIO,
    carpeta_copias: str,
    usuario: dict,
) -> dict[str, Any]:
    """Sustituye los catálogos y añade los archivos del ZIP. Lanza ``ZipInvalido`` si no vale."""
    try:
        z = zipfile.ZipFile(origen)
    except zipfile.BadZipFile:
        raise ZipInvalido("El archivo no es un ZIP válido.") from None
    with z:
        _, catalogos, nombres = validar_zip(z)

        # 1) Copia automática del estado actual (por si el usuario se equivoca de archivo)
        os.makedirs(carpeta_copias, exist_ok=True)
        sello = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        copia = os.path.join(carpeta_copias, f"antes_de_importar_{sello}.zip")
        with open(copia, "wb") as f:
            crear_zip(db, carpeta_uploads, f)

        # 2) Archivos: se escriben en una carpeta temporal y se mueven al final
        os.makedirs(carpeta_uploads, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix=".import_", dir=carpeta_uploads)
        try:
            escritos = 0
            for nombre in nombres:
                with z.open(CARPETA_ARCHIVOS + nombre) as src, open(
                    os.path.join(tmp, nombre), "wb"
                ) as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                escritos += 1

            # 3) Catálogos: sustitución con vuelta atrás si algo falla
            coleccion = db[COLECCION]
            anteriores = list(coleccion.find())
            nuevos = []
            for doc in catalogos:
                _asignar_propietario(doc, usuario)
                nuevos.append(doc)
            try:
                coleccion.delete_many({})
                if nuevos:
                    coleccion.insert_many(nuevos)
            except Exception:
                logger.exception("Fallo al importar: se restauran los catálogos anteriores")
                coleccion.delete_many({})
                if anteriores:
                    coleccion.insert_many(anteriores)
                raise

            for nombre in nombres:
                os.replace(os.path.join(tmp, nombre), os.path.join(carpeta_uploads, nombre))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return {"catalogos": len(nuevos), "archivos": escritos, "copia_previa": copia}
