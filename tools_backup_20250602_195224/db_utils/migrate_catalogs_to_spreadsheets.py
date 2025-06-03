#!/usr/bin/env python3
# Script: migrate_catalogs_to_spreadsheets.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 migrate_catalogs_to_spreadsheets.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- MIGRACIÓN DE catalogs -> spreadsheets (solo no existentes) ---')

migrados = 0
duplicados = 0
ids_migrados = []
ids_duplicados = []
for doc in db['catalogs'].find():
    nombre = doc.get('name')
    # Buscar por nombre en spreadsheets
    existe = db['spreadsheets'].find_one({'name': nombre})
    if existe:
        duplicados += 1
        ids_duplicados.append(str(doc['_id']))
        continue
    # Eliminar el _id para evitar conflicto
    doc_copia = dict(doc)
    doc_copia.pop('_id', None)
    db['spreadsheets'].insert_one(doc_copia)
    migrados += 1
    ids_migrados.append(str(doc['_id']))
    print(f"  - ID {doc['_id']}: migrado a spreadsheets")
print(f"✔ Catálogos migrados: {migrados}")
if ids_migrados:
    print(f"  IDs migrados: {ids_migrados}")
print(f"✔ Duplicados no migrados: {duplicados}")
if ids_duplicados:
    print(f"  IDs duplicados: {ids_duplicados}")
print('--- FIN DE LA MIGRACIÓN ---') 