#!/usr/bin/env python3
# Script: verify_catalogojoyero.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 verify_catalogojoyero.py [opciones]
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

# Solicitar usuario o email por input
user_input = input("Introduce el username o email a buscar: ").strip()

print(f"\n=== Verificando usuario '{user_input}' ===")
user = db['users'].find_one({
    '$or': [
        {'username': user_input},
        {'email': user_input}
    ]
})
if user:
    print(f"Usuario: {user.get('username', '-')}, Email: {user.get('email', '-')}, Rol: {user.get('role', '-')}")
else:
    print(f"Usuario '{user_input}' no encontrado en 'app_catalogojoyero_nueva.users'")

print("\n=== Verificando colecciones ===")
colecciones = ['users', 'catalogs', 'spreadsheets']
for col in colecciones:
    if col in db.list_collection_names():
        count = db[col].count_documents({})
        print(f"Colección '{col}': OK ({count} documentos)")
        if count == 0:
            print(f"  ⚠️ La colección '{col}' está vacía")
    else:
        print(f"Colección '{col}': NO EXISTE") 