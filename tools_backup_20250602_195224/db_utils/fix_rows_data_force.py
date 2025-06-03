#!/usr/bin/env python3
# Script: fix_rows_data_force.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 fix_rows_data_force.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- SINCRONIZACIÓN FORZADA rows/data EN CATÁLOGOS (AMBOS DIFERENTES) ---')

colecciones = [('catalogs', 'Catálogos'), ('spreadsheets', 'Spreadsheets')]
total_modificados = 0
for col, label in colecciones:
    modificados = 0
    ids_modificados = []
    for doc in db[col].find():
        rows = doc.get('rows')
        data = doc.get('data')
        if isinstance(rows, list) and isinstance(data, list) and rows != data:
            # Elegir el más largo
            if len(rows) >= len(data):
                update = {'data': rows}
                largo = len(rows)
            else:
                update = {'rows': data}
                largo = len(data)
            db[col].update_one({'_id': doc['_id']}, {'$set': update})
            modificados += 1
            ids_modificados.append(str(doc['_id']))
            print(f"  - ID {doc['_id']}: sincronizado, longitud final = {largo}")
    print(f"✔ {label}: {modificados} documentos sincronizados (ambos diferentes)")
    if ids_modificados:
        print(f"    IDs modificados: {ids_modificados}")
    total_modificados += modificados
print(f'--- FIN. Total modificados: {total_modificados} ---') 