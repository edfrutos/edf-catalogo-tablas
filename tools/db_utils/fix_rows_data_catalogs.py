#!/usr/bin/env python3
# Script: fix_rows_data_catalogs.py
# Descripción: Sincroniza los campos rows/data en catálogos o spreadsheets.
# Uso: python3 fix_rows_data_catalogs.py [--collection catalogs|spreadsheets|ambas]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description="Sincroniza los campos rows/data en catálogos o spreadsheets.")
parser.add_argument('--collection', choices=['catalogs', 'spreadsheets', 'ambas'], default='ambas', help="Colección a sincronizar (por defecto ambas)")
args = parser.parse_args()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- SINCRONIZACIÓN DE CAMPOS rows/data EN CATÁLOGOS ---')

if args.collection == 'ambas':
    colecciones = [('catalogs', 'Catálogos'), ('spreadsheets', 'Spreadsheets')]
else:
    label = 'Catálogos' if args.collection == 'catalogs' else 'Spreadsheets'
    colecciones = [(args.collection, label)]

total_modificados = 0
for col, label in colecciones:
    modificados = 0
    for doc in db[col].find():
        rows = doc.get('rows')
        data = doc.get('data')
        update = {}
        # Si solo existe uno de los dos y es lista, copiar al otro
        if isinstance(rows, list) and (not isinstance(data, list) or data is None):
            update['data'] = rows
        elif isinstance(data, list) and (not isinstance(rows, list) or rows is None):
            update['rows'] = data
        # Si ambos existen y son listas, y son diferentes, dejar el más largo en ambos
        elif isinstance(rows, list) and isinstance(data, list) and rows != data:
            if len(rows) >= len(data):
                update['data'] = rows
            else:
                update['rows'] = data
        if update:
            db[col].update_one({'_id': doc['_id']}, {'$set': update})
            modificados += 1
    print(f"✔ {label}: {modificados} documentos sincronizados")
    total_modificados += modificados
print(f'--- FIN. Total modificados: {total_modificados} ---') 