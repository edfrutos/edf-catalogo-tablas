#!/usr/bin/env python3
# Script: verify_app_catalogojoyero.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 verify_app_catalogojoyero.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from pymongo import MongoClient
import certifi
import os

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI no está definida en el entorno')

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['app_catalogojoyero_nueva']

print("\n=== Verificando usuario 'edefrutos' ===")
user = db['users'].find_one({'username': 'edefrutos'})
if user:
    print(f"Usuario: {user['username']}, Rol: {user.get('role')}, Email: {user.get('email')}")
else:
    print("Usuario 'edefrutos' no encontrado en 'app_catalogojoyero_nueva.users'")

print("\n=== Verificando colecciones ===")
colecciones = ['users', 'catalogs', 'spreadsheets']
for col in colecciones:
    if col in db.list_collection_names():
        count = db[col].count_documents({})
        print(f"Colección '{col}': OK ({count} documentos)")
        if count > 0:
            doc = db[col].find_one()
            print(f"  Ejemplo de documento: {doc}")
        else:
            print(f"  ⚠️ La colección '{col}' está vacía")
    else:
        print(f"Colección '{col}': NO EXISTE") 