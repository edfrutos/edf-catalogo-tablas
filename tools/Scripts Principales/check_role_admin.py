#!/usr/bin/env python3
# Script: check_role_admin.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 check_role_admin.py [opciones]
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
db = client.get_database()
users = db['users']

user = users.find_one({'username': 'edefrutos'})
if user:
    print(f"Usuario: {user['username']}, Rol actual: {user.get('role')}")
else:
    print("Usuario 'edefrutos' no encontrado.") 