#!/usr/bin/env python3
"""Diagnóstico puntual: inspecciona usuarios sin email/username/nombre y
comprueba si tienen catálogos/hojas de cálculo asociados por _id, antes de
decidir si son seguros de borrar. Solo lectura.

Uso: python3 tools/diagnostics/diag_check_orphan_users.py
"""
import os

import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGO_URI")
if not uri:
    raise SystemExit("No hay MONGO_URI en el entorno")

kwargs = {}
if uri.startswith("mongodb+srv"):
    kwargs["tlsCAFile"] = certifi.where()

client = MongoClient(uri, serverSelectionTimeoutMS=8000, **kwargs)
db = client.get_database()
print(f"Base: {db.name}\n")

users = db["users"]
print("=== Usuarios sin email/username/nombre ===")
orphans = list(
    users.find(
        {
            "$and": [
                {"$or": [{"email": {"$in": [None, ""]}}, {"email": {"$exists": False}}]},
                {"$or": [{"username": {"$in": [None, ""]}}, {"username": {"$exists": False}}]},
                {"$or": [{"nombre": {"$in": [None, ""]}}, {"nombre": {"$exists": False}}]},
            ]
        }
    )
)
if not orphans:
    print("  (ninguno encontrado con este criterio)")

for u in orphans:
    print(f"\n_id: {u['_id']}")
    for k, v in u.items():
        if k == "password":
            v = f"<{len(str(v))} chars, oculto>"
        print(f"  {k}: {v!r}")

    for coll_name in ["catalogs", "spreadsheets"]:
        if coll_name not in db.list_collection_names():
            continue
        coll = db[coll_name]
        by_id = coll.count_documents(
            {"$or": [{"owner_id": str(u["_id"])}, {"user_id": str(u["_id"])}, {"created_by_id": str(u["_id"])}]}
        )
        print(f"  Documentos en '{coll_name}' que referencian este _id: {by_id}")

print("\n=== Total usuarios en la base ===")
print(users.estimated_document_count())
