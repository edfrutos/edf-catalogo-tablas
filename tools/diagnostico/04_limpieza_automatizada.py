#!/usr/bin/env python3
# Script: 04_limpieza_automatizada.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 04_limpieza_automatizada.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
from collections import Counter, defaultdict

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv(
    "DB_NAME", "catalogo_tablas"
)  # Nombre por defecto de la base de datos
client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

print("--- LIMPIEZA AUTOMATIZADA (SÓLO SUGERENCIAS, NO BORRA NADA) ---")

# 1. Usuarios duplicados por email/username
users = list(db["users"].find())
emails = [u.get("email", "").lower() for u in users if u.get("email")]
usernames = [u.get("username", "").lower() for u in users if u.get("username")]

email_dups = defaultdict(list)
for u in users:
    email = u.get("email", "").lower()
    if email:
        email_dups[email].append(u)

username_dups = defaultdict(list)
for u in users:
    username = u.get("username", "").lower()
    if username:
        username_dups[username].append(u)

print("\nUsuarios duplicados por email:")
for email, us in email_dups.items():
    if len(us) > 1:
        print(f"- Email '{email}' tiene {len(us)} usuarios:")
        for u in us:
            print(
                f"   _id: {u.get('_id')}, username: {u.get('username')}, name: {u.get('name', '')} "
            )
        print(
            "  SUGERENCIA: Mantén solo uno y elimina los demás con: db.users.deleteOne({'_id': ObjectId('...')})"
        )

print("\nUsuarios duplicados por username:")
for username, us in username_dups.items():
    if len(us) > 1:
        print(f"- Username '{username}' tiene {len(us)} usuarios:")
        for u in us:
            print(
                f"   _id: {u.get('_id')}, email: {u.get('email')}, name: {u.get('name', '')} "
            )
        print(
            "  SUGERENCIA: Mantén solo uno y elimina los demás con: db.users.deleteOne({'_id': ObjectId('...')})"
        )

# 2. Catálogos/spreadsheets huérfanos
user_emails = set(emails)
user_usernames = set(usernames)


def listar_huerfanos(collection, label):
    huérfanos = []
    for doc in db[collection].find():
        owner = (
            doc.get("owner") or doc.get("created_by") or doc.get("owner_name") or ""
        ).lower()
        if owner and owner not in user_emails and owner not in user_usernames:
            huérfanos.append(
                {
                    "_id": str(doc.get("_id")),
                    "owner": owner,
                    "name": doc.get("name", ""),
                }
            )
    if huérfanos:
        print(f"\n{label} huérfanos:")
        for h in huérfanos:
            print(f"   - {h}")
        print(
            f"  SUGERENCIA: Elimina con: db.{collection}.deleteOne({{'_id': ObjectId('...')}}) o reasigna el owner a un usuario válido."
        )
    else:
        print(f"\nTodos los {label} tienen owner válido.")


listar_huerfanos("catalogs", "Catálogos")
listar_huerfanos("spreadsheets", "Spreadsheets")

print("\n--- FIN DE SUGERENCIAS DE LIMPIEZA ---")
