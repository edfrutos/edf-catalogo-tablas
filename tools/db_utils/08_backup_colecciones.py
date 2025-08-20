#!/usr/bin/env python3
# Script: 08_backup_colecciones.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 08_backup_colecciones.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import csv
import json
import os
from datetime import datetime

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

colecciones = ["users", "catalogs", "spreadsheets"]


def get_all_fieldnames(docs):
    fieldnames = set()
    for d in docs:
        fieldnames.update(d.keys())
    return list(fieldnames)


timestamp = datetime.now().strftime("%Y%m%d_%H%M")

for col in colecciones:
    docs = list(db[col].find())
    # Convertir ObjectId a str
    for d in docs:
        d["_id"] = str(d["_id"])
    # Backup JSON
    json_path = os.path.join(BACKUP_DIR, f"{col}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=4, ensure_ascii=False, default=str)
    print(f"✔ Backup JSON de {col} en {json_path}")
    # Backup CSV
    if docs:
        fieldnames = get_all_fieldnames(docs)
        csv_path = os.path.join(BACKUP_DIR, f"{col}_{timestamp}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in docs:
                # Rellenar con vacío los campos que falten
                row_filled = {k: row.get(k, "") for k in fieldnames}
                writer.writerow(row_filled)
        print(f"✔ Backup CSV de {col} en {csv_path}")
    else:
        print(f"⚠️ Colección {col} vacía, no se genera CSV.")
print("--- BACKUP COMPLETO ---")
