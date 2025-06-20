#!/usr/bin/env python3
# Script: update_role_admin.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 update_role_admin.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from pymongo import MongoClient
import certifi
import os

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI no está definida en el entorno')

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()
users = db['users']

import argparse

parser = argparse.ArgumentParser(description="Actualiza el rol de un usuario por email o username")
parser.add_argument('--email', help='Email del usuario')
parser.add_argument('--username', help='Username del usuario')
parser.add_argument('--role', default='admin', choices=['admin','normal'], help='Rol a asignar (admin o normal)')
parser.add_argument('--json', action='store_true', help='Salida en formato JSON')
args = parser.parse_args()

email = args.email or input('Email (dejar vacío si usas username): ') or None
username = args.username or (input('Username (opcional): ') if not email else None)
role = args.role
json_out = args.json

filtro = {}
if email:
    filtro['email'] = email
elif username:
    filtro['username'] = username
else:
    print('Debes indicar email o username')
    exit(1)

result = users.update_one(filtro, {'$set': {'role': role}})
if result.modified_count == 1:
    print("✅ Rol actualizado a admin para 'edefrutos'")
else:
    print("⚠️ No se actualizó ningún usuario. ¿Ya era admin o no existe?") 