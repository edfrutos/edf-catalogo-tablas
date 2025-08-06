#!/usr/bin/env python3
# Script: 03_validar_integridad.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 03_validar_integridad.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
import certifi
from pymongo import MongoClient
from collections import Counter
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "app_catalogojoyero_nueva")
client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

print("--- VALIDACIÓN DE INTEGRIDAD DE DATOS ---")

# 1. Emails y usernames duplicados en users
users = list(db["users"].find())
emails = [u.get("email", "").lower() for u in users if u.get("email")]
usernames = [u.get("username", "").lower() for u in users if u.get("username")]

dup_emails = [item for item, count in Counter(emails).items() if count > 1]
dup_usernames = [item for item, count in Counter(usernames).items() if count > 1]

if dup_emails:
    print(f"❌ Emails duplicados: {dup_emails}")
else:
    print("✔ No hay emails duplicados en users.")

if dup_usernames:
    print(f"❌ Usernames duplicados: {dup_usernames}")
else:
    print("✔ No hay usernames duplicados en users.")

# 2. Owners de catalogs y spreadsheets existen en users
user_emails = set(emails)
user_usernames = set(usernames)


def check_owners(collection, label):
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
        print(f"❌ {label} con owner/created_by huérfano:")
        for h in huérfanos:
            print(f"   - {h}")
    else:
        print(f"✔ Todos los {label} tienen owner válido.")


check_owners("catalogs", "catálogos")
check_owners("spreadsheets", "spreadsheets")

print("--- FIN DE LA VALIDACIÓN ---")
