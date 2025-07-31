#!/usr/bin/env python3
# Script: 07_eliminar_huerfanos.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 07_eliminar_huerfanos.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- ELIMINACIÓN AUTOMÁTICA DE HUÉRFANOS EN CATÁLOGOS Y SPREADSHEETS ---')

# Obtener emails y usernames válidos
user_emails = set(u['email'].lower() for u in db['users'].find() if u.get('email'))
user_usernames = set(u['username'].lower() for u in db['users'].find() if u.get('username'))

def eliminar_huerfanos(collection, label):
    huérfanos = []
    for doc in db[collection].find():
        owner = (doc.get('owner') or doc.get('created_by') or doc.get('owner_name') or '').lower()
        if owner and owner not in user_emails and owner not in user_usernames:
            huérfanos.append(doc['_id'])
    if huérfanos:
        result = db[collection].delete_many({'_id': {'$in': huérfanos}})
        print(f"✔ Eliminados {result.deleted_count} {label.lower()} huérfanos.")
    else:
        print(f"✔ No hay {label.lower()} huérfanos.")

eliminar_huerfanos('catalogs', 'Catálogos')
eliminar_huerfanos('spreadsheets', 'Spreadsheets')

print('--- FIN DE LA ELIMINACIÓN DE HUÉRFANOS ---') 