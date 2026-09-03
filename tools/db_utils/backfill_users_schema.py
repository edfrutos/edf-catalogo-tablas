#!/usr/bin/env python3
# Script: backfill_users_schema.py
# Descripción: Rellena en la colección `users` las claves que falten en cada
#              convención (snake_case para Flask, PascalCase para el cliente
#              .NET). Puramente aditivo: nunca sobrescribe un valor existente.
# Uso: python3 tools/db_utils/backfill_users_schema.py [--apply] [--env-file RUTA]
# Autor: EDF Developer - 2026-09-03
"""Backfill idempotente del esquema de `users`.

La colección `users` de ``edf_catalogotablas`` está compartida entre la app
Flask (snake_case) y el cliente .NET (PascalCase). Este script recorre todos
los documentos y, para cada uno:

* garantiza las claves canónicas snake_case (``username``, ``nombre``, ``role``,
  ``is_active``...) a partir de las PascalCase existentes;
* garantiza el espejo PascalCase (``Username``, ``Name``, ``Role``...) a partir
  de las snake_case existentes.

Solo **añade** claves que faltan; si una clave ya tiene valor no se toca. Es
idempotente: ejecutarlo dos veces no cambia nada la segunda vez.

Por defecto hace *dry-run* (solo informa). Con ``--apply`` escribe.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models.user_schema import (  # noqa: E402
    SNAKE_TO_PASCAL,
    USER_FIELD_ALIASES,
    normalize_user_doc,
)


def _mask_email(email: str | None) -> str:
    if not email or "@" not in str(email):
        return str(email)
    user, _, domain = str(email).partition("@")
    head = user[:2] if len(user) > 2 else user
    return f"{head}***@{domain}"


def _is_empty(value: object) -> bool:
    return value is None or value == ""


def compute_set(doc: dict) -> dict:
    """Devuelve el ``$set`` aditivo para un documento (solo claves ausentes)."""
    norm = normalize_user_doc(doc) or {}
    set_ops: dict = {}

    # 1. Claves canónicas snake_case que falten en el documento almacenado.
    for canonical in USER_FIELD_ALIASES:
        if _is_empty(doc.get(canonical)) and not _is_empty(norm.get(canonical)):
            set_ops[canonical] = norm[canonical]

    # 2. Espejo PascalCase que falte (no se toca si ya existe, aunque difiera).
    for snake, pascal in SNAKE_TO_PASCAL.items():
        source = doc.get(snake)
        if _is_empty(source):
            source = norm.get(snake)
        if _is_empty(doc.get(pascal)) and not _is_empty(source):
            set_ops[pascal] = source

    return set_ops


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Escribe los cambios (por defecto dry-run)"
    )
    parser.add_argument("--env-file", help="Ruta al .env (por defecto ./.env o autodetección)")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
    except ImportError:
        print("❌ Falta python-dotenv (pip install python-dotenv)")
        return 2

    if args.env_file:
        load_dotenv(args.env_file)
    else:
        default_env = REPO_ROOT / ".env"
        load_dotenv(default_env if default_env.exists() else None)

    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI no está definida (usa --env-file)")
        return 2

    from pymongo import MongoClient

    db = MongoClient(mongo_uri).get_database()
    col = db["users"]
    total = col.estimated_document_count()
    print(f"BD: {db.name} · colección: users · documentos: {total}")
    print(f"Modo: {'APPLY (escribe)' if args.apply else 'DRY-RUN (solo informa)'}\n")

    changed = 0
    for doc in col.find({}):
        set_ops = compute_set(doc)
        if not set_ops:
            continue
        changed += 1
        ident = _mask_email(doc.get("email") or doc.get("Username") or doc.get("username"))
        print(f"· {ident}  ->  +{sorted(set_ops.keys())}")
        if args.apply:
            col.update_one({"_id": doc["_id"]}, {"$set": set_ops})

    print(f"\n{'Actualizados' if args.apply else 'Se actualizarían'}: {changed}/{total}")
    if changed and not args.apply:
        print("Vuelve a ejecutar con --apply para escribir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
