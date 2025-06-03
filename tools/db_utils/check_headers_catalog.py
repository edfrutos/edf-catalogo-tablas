#!/usr/bin/env python3
# Script: check_headers_catalog.py
# Descripción: Comprueba los headers de un catálogo por su ObjectId
# Uso: python3 check_headers_catalog.py --catalog_id <ObjectId>
# Autor: [Tu nombre o equipo] - 2025-05-28

from pymongo import MongoClient
from bson import ObjectId
import os
import argparse

parser = argparse.ArgumentParser(description="Comprueba los headers de un catálogo por su ObjectId")
parser.add_argument('--catalog_id', required=True, help="ObjectId del catálogo a comprobar")
args = parser.parse_args()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI no está definida en el entorno')

client = MongoClient(MONGO_URI)
db = client.get_default_database()
if db is None:
    db = client['app_catalogojoyero_nueva']

catalog_id = args.catalog_id

for collection_name in ['catalogs', 'spreadsheets']:
    print(f"\nBuscando en colección: {collection_name}")
    try:
        cat = db[collection_name].find_one({"_id": ObjectId(catalog_id)})
        if cat:
            print(f"Encontrado. headers = {cat.get('headers')}")
        else:
            print("No encontrado.")
    except Exception as e:
        print(f"Error consultando {collection_name}: {e}") 