#!/usr/bin/env python3
# Script: fix_headers_catalogs.py
# Descripción: Repara los encabezados de la colección indicada (por defecto 'catalogs').
# Uso: python3 fix_headers_catalogs.py [--collection catalogs]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description="Repara los encabezados de la colección indicada (por defecto 'catalogs').")
parser.add_argument('--collection', default='catalogs', help="Nombre de la colección a reparar (por defecto 'catalogs')")
args = parser.parse_args()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

collection = db[args.collection]
print(f'--- REPARACIÓN DE ENCABEZADOS EN COLECCIÓN {args.collection} ---')

modificados = 0
ids_modificados = []
for doc in collection.find():
    headers = doc.get('headers')
    # Si no hay headers o está vacío
    if not headers or not isinstance(headers, list) or len(headers) == 0:
        # Buscar la primera fila de datos
        filas = doc.get('rows') or doc.get('data')
        if isinstance(filas, list) and len(filas) > 0 and isinstance(filas[0], dict):
            nuevos_headers = list(filas[0].keys())
        else:
            nuevos_headers = []
        collection.update_one({'_id': doc['_id']}, {'$set': {'headers': nuevos_headers}})
        print(f"  - ID {doc['_id']}: headers reconstruidos -> {nuevos_headers}")
        modificados += 1
        ids_modificados.append(str(doc['_id']))
print(f"✔ Documentos modificados: {modificados}")
if ids_modificados:
    print(f"  IDs modificados: {ids_modificados}")
print(f'--- FIN DE LA REPARACIÓN EN {args.collection} ---') 