#!/usr/bin/env python3
# Script: debug_users.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 debug_users.py [opciones]
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

print("=== Bases de datos disponibles ===")
for db_name in client.list_database_names():
    print(f"- {db_name}")
    db = client[db_name]
    if 'users' in db.list_collection_names():
        print(f"  -> Colección 'users' encontrada en {db_name}")
        users = db['users']
        print("    > Usuarios por username='edefrutos':")
        for user in users.find({'username': 'edefrutos'}):
            print(f"      {user}")
        print("    > Usuarios por email='edfrutos@gmail.com':")
        for user in users.find({'email': 'edfrutos@gmail.com'}):
            print(f"      {user}")
        print("    > Usuarios por nombre='edefrutos':")
        for user in users.find({'nombre': 'edefrutos'}):
            print(f"      {user}")
    else:
        print(f"  -> Colección 'users' NO encontrada en {db_name}") 