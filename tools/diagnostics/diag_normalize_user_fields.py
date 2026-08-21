#!/usr/bin/env python3
"""Normaliza a minúscula los campos de usuarios que quedaron con esquema
PascalCase (Email, Username, Name, Password, Role, IsActive, CreatedAt,
ProfileImageUrl, FullName, Phone, Company, Address, Occupation, LastLoginAt,
UpdatedAt) en vez del esquema en minúscula que usa el resto de la app
(email, username, nombre, password, role, active, created_at, ...).

No borra ni pisa ningún campo en minúscula que ya exista -- solo actúa
sobre documentos que tienen la versión en mayúscula pero no la equivalente
en minúscula. Es seguro ejecutarlo más de una vez (idempotente): $rename
sobre un campo que ya no existe no hace nada.

Por defecto corre en modo simulación (no escribe nada). Pasa --apply para
aplicar los cambios de verdad.

Uso:
    python3 tools/diagnostics/fix_orphan_user_fields.py            # dry-run
    python3 tools/diagnostics/fix_orphan_user_fields.py --apply    # aplica
"""
import os
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

# Campo en mayúscula -> campo en minúscula que usa el resto de la app.
# Los campos "extra" (sin equivalente ya existente en otros usuarios) se
# preservan bajo un nombre nuevo en minúscula en vez de perderse.
FIELD_MAP = {
    "Email": "email",
    "Username": "username",
    "Name": "nombre",
    "Password": "password",
    "Role": "role",
    "IsActive": "active",
    "CreatedAt": "created_at",
    "UpdatedAt": "updated_at",
    "LastLoginAt": "last_login",
    "ProfileImageUrl": "profile_image_url",
    "FullName": "full_name",
    "Phone": "phone",
    "Company": "company",
    "Address": "address",
    "Occupation": "occupation",
}

candidates = list(
    users.find(
        {
            "Email": {"$exists": True},
            "email": {"$exists": False},
        }
    )
)

if not candidates:
    print("No hay usuarios con esquema PascalCase pendientes de normalizar.")
    sys.exit(0)

print(f"{'[APLICANDO]' if APPLY else '[SIMULACIÓN -- usa --apply para escribir]'}")
print(f"Usuarios a normalizar: {len(candidates)}\n")

for u in candidates:
    rename_ops = {old: new for old, new in FIELD_MAP.items() if old in u}
    print(f"_id={u['_id']}  ({u.get('Email')})")
    for old, new in rename_ops.items():
        print(f"  {old} -> {new}")
    if APPLY:
        result = users.update_one({"_id": u["_id"]}, {"$rename": rename_ops})
        print(f"  modified_count={result.modified_count}")
    print()

if not APPLY:
    print("Nada escrito (modo simulación). Repite con --apply para aplicar de verdad.")
