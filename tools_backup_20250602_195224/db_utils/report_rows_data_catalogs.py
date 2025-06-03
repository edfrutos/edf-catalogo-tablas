#!/usr/bin/env python3
# Script: report_rows_data_catalogs.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 report_rows_data_catalogs.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- INFORME DE CONSISTENCIA rows/data EN CATÁLOGOS ---')

colecciones = [('catalogs', 'Catálogos'), ('spreadsheets', 'Spreadsheets')]
for col, label in colecciones:
    solo_rows = []
    solo_data = []
    ambos_iguales = []
    ambos_diferentes = []
    ninguno = []
    for doc in db[col].find():
        _id = str(doc['_id'])
        rows = doc.get('rows')
        data = doc.get('data')
        if isinstance(rows, list) and (not isinstance(data, list) or data is None):
            solo_rows.append(_id)
        elif isinstance(data, list) and (not isinstance(rows, list) or rows is None):
            solo_data.append(_id)
        elif isinstance(rows, list) and isinstance(data, list):
            if rows == data:
                ambos_iguales.append(_id)
            else:
                ambos_diferentes.append(_id)
        else:
            ninguno.append(_id)
    print(f"\nColección: {label}")
    print(f"  Solo 'rows': {len(solo_rows)}")
    print(f"  Solo 'data': {len(solo_data)}")
    print(f"  Ambos iguales: {len(ambos_iguales)}")
    print(f"  Ambos diferentes: {len(ambos_diferentes)}")
    print(f"  Ninguno: {len(ninguno)}")
    if ambos_diferentes:
        print(f"    IDs con ambos diferentes: {ambos_diferentes}")
    if solo_rows:
        print(f"    IDs solo 'rows': {solo_rows}")
    if solo_data:
        print(f"    IDs solo 'data': {solo_data}")
    if ninguno:
        print(f"    IDs sin filas: {ninguno}")
print('\n--- FIN DEL INFORME ---') 