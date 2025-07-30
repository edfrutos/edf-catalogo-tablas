#!/usr/bin/env python3
# Script: 05_reasignar_owners_huerfanos.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 05_reasignar_owners_huerfanos.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- REASIGNACIÓN DE OWNERS HUÉRFANOS ---')

admin_owner = input('Introduce el email o username del usuario admin al que reasignar los huérfanos: ').strip().lower()

# Verificar que el usuario admin existe
def user_exists(owner):
    return db['users'].find_one({'$or': [
        {'email': owner},
        {'username': owner}
    ]}) is not None

if not user_exists(admin_owner):
    print(f"❌ El usuario '{admin_owner}' no existe en la colección users. Aborta.")
    exit(1)

user_emails = set(u['email'].lower() for u in db['users'].find() if u.get('email'))
user_usernames = set(u['username'].lower() for u in db['users'].find() if u.get('username'))

colecciones = [('catalogs', 'Catálogos'), ('spreadsheets', 'Spreadsheets')]

for col, label in colecciones:
    huérfanos = []
    for doc in db[col].find():
        owner = (doc.get('owner') or doc.get('created_by') or doc.get('owner_name') or '').lower()
        if owner and owner not in user_emails and owner not in user_usernames:
            huérfanos.append(doc['_id'])
    if huérfanos:
        result = db[col].update_many({'_id': {'$in': huérfanos}}, {'$set': {'owner': admin_owner, 'created_by': admin_owner, 'owner_name': admin_owner}})
        print(f"✔ Reasignados {result.modified_count} {label.lower()} huérfanos a '{admin_owner}'")
    else:
        print(f"✔ No hay {label.lower()} huérfanos.")

print('--- FIN DE LA REASIGNACIÓN ---') 