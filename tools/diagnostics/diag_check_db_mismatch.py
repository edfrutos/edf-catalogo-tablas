#!/usr/bin/env python3
"""Diagnóstico puntual: compara la base de datos que usa app/database.py
(get_database() sin argumento, es decir la del propio MONGO_URI) contra la que
usa app/models/database.py (MONGODB_DB env var). No escribe nada, solo lee.

Uso: python3 tools/diag_check_db_mismatch.py
"""
import os

import certifi
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

uri_db = client.get_database()  # la que usa app/database.py
env_db_name = os.getenv("MONGODB_DB", "app_catalogojoyero_nueva")
env_db = client[env_db_name]  # la que usa app/models/database.py

print(f"Base según el propio URI (app/database.py):      {uri_db.name}")
print(f"Base según MONGODB_DB (app/models/database.py):  {env_db_name}")
print(f"¿Son la misma? {'SI' if uri_db.name == env_db_name else 'NO -> aquí está el bug'}")
print()
print("Bases de datos visibles en el cluster:")
for name in client.list_database_names():
    print(f"  - {name}")
print()


def describe_hash(pw):
    if not pw:
        return "SIN CAMPO password"
    if pw.startswith("scrypt:"):
        parts = pw.split("$")
        hv = parts[2] if len(parts) > 2 else ""
        enc = "hex" if hv and all(c in "0123456789abcdef" for c in hv.lower()) else "base64/otro"
        return f"scrypt | method={parts[0]} | hashval_enc={enc}"
    if pw.startswith("pbkdf2:"):
        return f"pbkdf2 | {pw.split('$')[0]}"
    if pw.startswith(("$2a$", "$2b$", "$2y$")):
        return "bcrypt"
    return f"desconocido | len={len(pw)}"


for label, db in [("URI (edf_catalogotablas esperado)", uri_db), (f"MONGODB_DB ({env_db_name})", env_db)]:
    print(f"--- Base: {label} ---")
    if "users" not in db.list_collection_names():
        print("  (no existe colección 'users' en esta base)")
        continue
    users = db["users"]
    print(f"  Documentos en 'users': {users.estimated_document_count()}")
    import re

    q = {
        "$or": [
            {"email": re.compile("admin|edefrutos", re.I)},
            {"username": re.compile("admin|edefrutos", re.I)},
            {"nombre": re.compile("admin|edefrutos", re.I)},
        ]
    }
    found = list(users.find(q))
    if not found:
        print("  No se encontró admin/edefrutos en esta base.")
    for u in found:
        print(
            f"  -> username={u.get('username')!r} email={u.get('email')!r} "
            f"role={u.get('role')} password: {describe_hash(u.get('password'))}"
        )
    print()
