# Script: maintenance.py
# Descripción: [Módulo para mantenimiento de la base de datos. Permite normalizar campos de usuarios y realizar backups.]
# Uso: python3 maintenance.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

import json
import logging
import os
from datetime import datetime

from app.models import get_users_collection

logger = logging.getLogger(__name__)


def normalize_user_fields(user):
    """Normaliza los campos username, email y nombre de un usuario (strip y lower)."""
    changed = {}
    for field in ["username", "email", "nombre"]:
        if field in user and isinstance(user[field], str):
            original = user[field]
            normalized = original.strip()
            if field in ["username", "email"]:
                normalized = normalized.lower()
            if normalized != original:
                changed[field] = (original, normalized)
                user[field] = normalized
    return changed


def backup_users_to_json(collection, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)
    users = list(collection.find())
    backup_file = os.path.join(
        backup_dir, f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2, default=str)
    return backup_file, len(users)


def normalize_users_in_db(apply_changes=False, logger=logger):
    """
    Normaliza los campos username, email y nombre de todos los usuarios en la colección.
    Si apply_changes=False, solo muestra un resumen de los cambios (dry-run).
    Si apply_changes=True, actualiza los documentos en la base de datos.
    Devuelve un resumen de la operación.
    """
    collection = get_users_collection()
    if collection is None:
        logger.error("No se pudo obtener la colección de usuarios")
        return {"error": "No se pudo obtener la colección de usuarios"}

    users = list(collection.find())
    changed_users = []
    for user in users:
        changes = normalize_user_fields(user)
        if changes:
            changed_users.append({"_id": str(user["_id"]), "changes": changes})
            if apply_changes:
                collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {k: v[1] for k, v in changes.items()}},
                )

    summary = {
        "total_users": len(users),
        "users_changed": len(changed_users),
        "changes": changed_users[:20],  # muestra solo los primeros 20 para resumen
    }
    return summary
