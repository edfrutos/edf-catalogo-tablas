# Script: admin_backup_restore_utils.py
# Descripción: Utilidades compartidas para leer, validar y preparar backups de restauración.

import gzip
import json
from pathlib import Path
from typing import Any, Dict, List

from bson import ObjectId


class BackupRestoreError(ValueError):
    """Error controlado durante lectura o validación de backups."""


def is_mongodb_binary_dump_name(filename: str) -> bool:
    """Detecta por nombre backups binarios de MongoDB no restaurables por JSON."""
    return filename.startswith("mongodb_backup_")


def looks_like_mongodb_binary_dump(content: str) -> bool:
    """Detecta señales típicas de un dump binario o metadatos de mongodump."""
    lowered = content.lower()
    return (
        content.startswith("BSON")
        or "mongodump" in lowered
        or "concurrent_collections" in content
        or "server_version" in content
    )


def _decode_bytes(raw: bytes) -> str:
    """Decodifica bytes de backup usando UTF-8 y fallback latin-1."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise BackupRestoreError(
                "No se pudo decodificar el contenido del archivo comprimido"
            ) from exc


def read_backup_json_file(file_path: str | Path) -> Any:
    """
    Lee un backup local JSON o JSON.GZ y devuelve el objeto parseado.

    Acepta:
    - JSON plano
    - GZIP con JSON dentro

    Rechaza:
    - dumps binarios de MongoDB
    - contenido no JSON
    """
    path = Path(file_path)

    if not path.exists():
        raise BackupRestoreError(f"El archivo de backup {path.name} no existe")

    try:
        with path.open("rb") as file:
            magic_bytes = file.read(2)

        if magic_bytes.startswith(b"\x1f\x8b"):
            try:
                with gzip.open(path, "rb") as gz_file:
                    raw = gz_file.read()
                content = _decode_bytes(raw)
            except OSError as exc:
                raise BackupRestoreError(
                    f"Error al descomprimir el archivo GZIP: {str(exc)}"
                ) from exc
        else:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = path.read_text(encoding="latin-1")
                except UnicodeDecodeError as exc:
                    raise BackupRestoreError(
                        f"Formato de archivo no válido: {str(exc)}"
                    ) from exc

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            if looks_like_mongodb_binary_dump(content):
                raise BackupRestoreError(
                    "Este archivo es un backup binario de MongoDB (mongodump). "
                    "Solo se pueden restaurar backups en formato JSON. "
                    "Use el archivo backup_*.json.gz en su lugar."
                ) from exc

            raise BackupRestoreError(
                f"El archivo de backup no contiene JSON válido. Error: {str(exc)}"
            ) from exc

    except BackupRestoreError:
        raise
    except OSError as exc:
        raise BackupRestoreError(
            f"Error al procesar el archivo: {str(exc)}") from exc


def extract_catalog_documents(backup_data: Any) -> List[Dict[str, Any]]:
    """
    Extrae la lista de documentos de catálogo desde un backup.

    Acepta:
    - lista directa de documentos
    - estructura nueva con collections.catalogs
    """
    if not backup_data:
        raise BackupRestoreError("No se pudo procesar el contenido del backup")

    if isinstance(backup_data, dict):
        collections = backup_data.get("collections")
        if isinstance(collections, dict) and isinstance(collections.get("catalogs"), list):
            return collections["catalogs"]

        raise BackupRestoreError(
            "El backup no contiene la estructura esperada")

    if isinstance(backup_data, list):
        return backup_data

    raise BackupRestoreError(
        "El backup debe contener una lista de documentos o una estructura válida"
    )


def prepare_restore_documents(backup_data: Any) -> List[Dict[str, Any]]:
    """
    Prepara documentos para restauración:
    - extrae catalogs
    - convierte _id string a ObjectId
    - descarta elementos que no sean dict
    """
    catalogs = extract_catalog_documents(backup_data)
    processed_docs: List[Dict[str, Any]] = []

    for doc in catalogs:
        if not isinstance(doc, dict):
            continue

        converted_doc = dict(doc)

        if "_id" in converted_doc and isinstance(converted_doc["_id"], str):
            try:
                converted_doc["_id"] = ObjectId(converted_doc["_id"])
            except Exception:
                converted_doc["_id"] = ObjectId()

        processed_docs.append(converted_doc)

    if not processed_docs:
        raise BackupRestoreError(
            "No se encontraron documentos válidos en el backup")

    return processed_docs
