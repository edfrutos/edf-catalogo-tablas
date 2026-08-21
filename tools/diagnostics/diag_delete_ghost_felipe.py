#!/usr/bin/env python3
"""Elimina el usuario "fantasma" felipe@catalog.com / felipe@catalog.web.

Su campo _id no es un ObjectId real sino el texto literal
'ObjectId("6a3ab5000ed78be860000000")' (probablemente de una importación
mal hecha), por lo que las rutas normales de editar/eliminar del panel de
admin (que hacen ObjectId(user_id) para buscarlo) nunca lo encuentran.

Este script lo localiza por email (sirve para .com o .web) y lo borra
usando el valor exacto de su _id tal como está almacenado, sea cual sea
su tipo real. Antes de borrar comprueba que no tenga catálogos/hojas de
cálculo asociados.

Por defecto corre en modo simulación. Pasa --apply para borrar de verdad.

Uso:
    python3 tools/diagnostics/diag_delete_ghost_felipe.py            # dry-run
    python3 tools/diagnostics/diag_delete_ghost_felipe.py --apply    # borra
"""
import os
import re
import sys

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

APPLY = "--apply" in sys.argv

uri = os.getenv("MONGO_URI")
if not uri:
    raise SystemExit("No hay MONGO_URI en el entorno")

kwargs = {}
if uri.startswith("mongodb+srv"):
    kwargs["tlsCAFile"] = certifi.where()

client = MongoClient(uri, serverSelectionTimeoutMS=8000, **kwargs)
db = client.get_database()
users = db["users"]

candidates = list(users.find({"email": re.compile(r"^felipe@catalog\.(com|web)$", re.I)}))

if not candidates:
    print("No se encontró ningún usuario felipe@catalog.com/.web. Nada que hacer.")
    sys.exit(0)

if len(candidates) > 1:
    print(f"ADVERTENCIA: se encontraron {len(candidates)} coincidencias, no solo 1.")
    for u in candidates:
        print(f"  _id={u['_id']!r} email={u.get('email')!r}")
    print("Abortando por seguridad -- revisa manualmente.")
    sys.exit(1)

user = candidates[0]
raw_id = user["_id"]
print(f"Encontrado: email={user.get('email')!r} nombre={user.get('nombre')!r}")
print(f"_id real almacenado: {raw_id!r} (tipo: {type(raw_id).__name__})")

for coll_name in ["catalogs", "spreadsheets"]:
    if coll_name not in db.list_collection_names():
        continue
    coll = db[coll_name]
    count = coll.count_documents(
        {"$or": [{"owner_id": raw_id}, {"user_id": raw_id}, {"created_by_id": raw_id},
                 {"owner_id": str(raw_id)}, {"user_id": str(raw_id)}, {"created_by_id": str(raw_id)}]}
    )
    print(f"Documentos en '{coll_name}' que lo referencian: {count}")
    if count > 0:
        print(f"ABORTANDO: tiene {count} documentos asociados en {coll_name}, no se borra automáticamente.")
        sys.exit(1)

if not APPLY:
    print("\n[SIMULACIÓN] Se borraría este documento. Repite con --apply para borrar de verdad.")
    sys.exit(0)

result = users.delete_one({"_id": raw_id})
print(f"\n[APLICADO] delete_one -> deleted_count={result.deleted_count}")
