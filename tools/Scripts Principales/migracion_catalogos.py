#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

client = MongoClient(MONGO_URI)
db = client['app_catalogojoyero_nueva']  # Cambia si tu base de datos tiene otro nombre
spreadsheets_collection = db['spreadsheets']

# Buscar documentos sin 'name'
unnamed_tables = spreadsheets_collection.find({"name": {"$exists": False}})
count = 0

for table in unnamed_tables:
    filename = table.get('filename', 'sin_nombre.xlsx')
    new_name = f"Catálogo {filename}"
    result = spreadsheets_collection.update_one(
        {"_id": table["_id"]},
        {"$set": {"name": new_name}}
    )
    if result.modified_count > 0:
        print(f"Actualizado: {new_name}")
        count += 1

print(f"\nActualización completada. {count} catálogos/tablas actualizados.")
client.close()