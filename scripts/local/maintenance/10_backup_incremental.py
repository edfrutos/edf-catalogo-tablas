#!/usr/bin/env python3
# Script: 10_backup_incremental.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 10_backup_incremental.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import json
import os
from datetime import datetime, timezone

import certifi
from bson import ObjectId
from pymongo import MongoClient

from tools.db_utils.google_drive_utils import upload_to_drive

MONGO_URI = os.getenv("MONGO_URI")
client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

BACKUP_DIR = "backups"
STATE_FILE = os.path.join(BACKUP_DIR, "incremental_state.json")
os.makedirs(BACKUP_DIR, exist_ok=True)


def get_last_backup_time():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
            return datetime.fromisoformat(state.get("last_backup"))
    return None


def set_last_backup_time(dt):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_backup": dt.isoformat()}, f)


def get_objectid_datetime(oid):
    if isinstance(oid, ObjectId):
        return oid.generation_time.replace(tzinfo=timezone.utc)
    try:
        return ObjectId(oid).generation_time.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def backup_incremental(since=None):
    now = datetime.now(timezone.utc)
    collections = db.list_collection_names()
    report = []
    uploaded_links = []
    for col in collections:
        query = {}
        if since:
            # Preferimos updated_at si existe
            sample = db[col].find_one(sort=[("_id", -1)])
            if sample and "updated_at" in sample:
                query = {"updated_at": {"$gt": since.isoformat()}}
            else:
                # Usar _id por timestamp
                min_oid = ObjectId.from_datetime(since)
                query = {"_id": {"$gt": min_oid}}
        docs = list(db[col].find(query))
        for d in docs:
            d["_id"] = str(d["_id"])
        if docs:
            ts = now.strftime("%Y%m%d_%H%M")
            fname = f"{col}_incremental_{ts}.json"
            path = os.path.join(BACKUP_DIR, fname)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(docs, f, indent=4, ensure_ascii=False, default=str)
            report.append(f"✔ Backup incremental de {col}: {len(docs)} docs en {fname}")
            # Subir a Google Drive
            link = upload_to_drive(path)
            uploaded_links.append(f"{fname}: {link}")
        else:
            report.append(f"⚠️ Sin cambios en {col} desde {since}")
    set_last_backup_time(now)
    print("\n".join(report))
    if uploaded_links:
        print("--- ENLACES DE DESCARGA EN GOOGLE DRIVE ---")
        print("\n".join(uploaded_links))
    print("--- BACKUP INCREMENTAL COMPLETO ---")


if __name__ == "__main__":
    print("--- BACKUP INCREMENTAL ---")
    last = get_last_backup_time()
    print(f"Último backup incremental: {last}")
    custom = input(
        "¿Forzar backup desde una fecha concreta? (YYYY-MM-DD HH:MM, vacío para no): "
    ).strip()
    if custom:
        since = datetime.fromisoformat(custom)
    else:
        since = last
    backup_incremental(since)
