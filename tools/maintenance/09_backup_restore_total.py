#!/usr/bin/env python3
# Script: 09_backup_restore_total.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 09_backup_restore_total.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import csv
import json
import os
import zipfile
from datetime import datetime

import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)


def get_all_fieldnames(docs):
    fieldnames = set()
    for d in docs:
        fieldnames.update(d.keys())
    return list(fieldnames)


def backup_all_collections():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    collections = db.list_collection_names()
    report = []
    backup_files = []
    for col in collections:
        docs = list(db[col].find())
        for d in docs:
            d["_id"] = str(d["_id"])
        # JSON
        json_path = os.path.join(BACKUP_DIR, f"{col}_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=4, ensure_ascii=False, default=str)
        report.append(f"✔ Backup JSON de {col} en {json_path}")
        backup_files.append(json_path)
        # CSV
        if docs:
            fieldnames = get_all_fieldnames(docs)
            csv_path = os.path.join(BACKUP_DIR, f"{col}_{timestamp}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in docs:
                    row_filled = {k: row.get(k, "") for k in fieldnames}
                    writer.writerow(row_filled)
            report.append(f"✔ Backup CSV de {col} en {csv_path}")
            backup_files.append(csv_path)
        else:
            report.append(f"⚠️ Colección {col} vacía, no se genera CSV.")
    # Comprimir todos los backups en un zip
    zip_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in backup_files:
            zipf.write(file, arcname=os.path.basename(file))
    print("\n".join(report))
    print(f"✔ Todos los backups comprimidos en {zip_path}")
    print("--- BACKUP COMPLETO ---")


def restore_collection():
    json_file = input(
        "Introduce el nombre del archivo .json de backup a restaurar (en backups/): "
    ).strip()
    collection_name = input("Introduce el nombre de la colección destino: ").strip()
    path = os.path.join(BACKUP_DIR, json_file)
    if not os.path.exists(path):
        print(f"❌ Archivo {path} no encontrado.")
        return
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)
    from bson import ObjectId

    n_upserted = 0
    for d in docs:
        if "_id" in d:
            try:
                d["_id"] = ObjectId(d["_id"])
            except Exception:
                pass
        # Upsert por _id
        result = db[collection_name].replace_one({"_id": d.get("_id")}, d, upsert=True)
        n_upserted += result.upserted_id is not None or result.modified_count > 0
    print(
        f"✔ Restaurados/actualizados {n_upserted} documentos en la colección {collection_name}"
    )
    print("--- RESTAURACIÓN COMPLETA ---")


def restore_multiple_collections():
    print("Archivos .json disponibles en backups/:")
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
    for i, f in enumerate(files):
        print(f"{i + 1}. {f}")
    indices = input(
        "Introduce los números de los archivos a restaurar separados por coma (ej: 1,3,5): "
    ).strip()
    indices = [int(x) - 1 for x in indices.split(",") if x.strip().isdigit()]
    for idx in indices:
        if 0 <= idx < len(files):
            json_file = files[idx]
            collection_name = input(f"Colección destino para {json_file}: ").strip()
            path = os.path.join(BACKUP_DIR, json_file)
            with open(path, encoding="utf-8") as f:
                docs = json.load(f)
            from bson import ObjectId

            n_upserted = 0
            for d in docs:
                if "_id" in d:
                    try:
                        d["_id"] = ObjectId(d["_id"])
                    except Exception:
                        pass
                result = db[collection_name].replace_one(
                    {"_id": d.get("_id")}, d, upsert=True
                )
                n_upserted += (
                    result.upserted_id is not None or result.modified_count > 0
                )
            print(
                f"✔ Restaurados/actualizados {n_upserted} documentos en {collection_name} desde {json_file}"
            )
    print("--- RESTAURACIÓN MÚLTIPLE COMPLETA ---")


print("¿Qué acción deseas realizar?")
print("1. Backup de todas las colecciones")
print("2. Restaurar una colección desde backup .json")
print("3. Restaurar varias colecciones desde backups .json")
accion = input("Introduce 1, 2 o 3: ").strip()
if accion == "1":
    backup_all_collections()
elif accion == "2":
    restore_collection()
elif accion == "3":
    restore_multiple_collections()
else:
    print("Acción no reconocida.")
