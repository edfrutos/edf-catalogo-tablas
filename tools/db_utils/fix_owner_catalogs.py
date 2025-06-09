#!/usr/bin/env python3
# Script: fix_owner_catalogs.py
# Descripción: Reasigna el propietario de catálogos/tablas de un usuario a otro.
# Uso: python3 fix_owner_catalogs.py --old_owner <email/username> --new_owner <email/username>
# Autor: EDF Equipo de Desarrollo - 2025-05-28

import os
import certifi
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description="Reasigna el propietario de catálogos/tablas de un usuario a otro.")
parser.add_argument('--old_owner', required=True, help="Email o username ACTUAL del propietario a corregir")
parser.add_argument('--new_owner', required=True, help="Email o username NUEVO propietario")
args = parser.parse_args()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- REASIGNACIÓN DE PROPIETARIO DE CATÁLOGOS ---')

old_owner = args.old_owner.strip().lower()
new_owner = args.new_owner.strip().lower()

# Verificar que el nuevo propietario existe
user = db['users'].find_one({'$or': [
    {'email': new_owner},
    {'username': new_owner}
]})
if not user:
    print(f"❌ El usuario '{new_owner}' no existe en la colección users. Aborta.")
    exit(1)

colecciones = [('catalogs', 'Catálogos'), ('spreadsheets', 'Spreadsheets')]

total_modificados = 0
for col, label in colecciones:
    query = {'$or': [
        {'owner': old_owner},
        {'created_by': old_owner},
        {'owner_name': old_owner}
    ]}
    docs = list(db[col].find(query))
    if docs:
        ids = [doc['_id'] for doc in docs]
        result = db[col].update_many({'_id': {'$in': ids}}, {'$set': {'owner': new_owner, 'created_by': new_owner, 'owner_name': new_owner}})
        print(f"✔ Reasignados {result.modified_count} {label.lower()} de '{old_owner}' a '{new_owner}'")
        total_modificados += result.modified_count
    else:
        print(f"✔ No hay {label.lower()} de '{old_owner}' a reasignar.")

print(f'--- FIN. Total modificados: {total_modificados} ---') 