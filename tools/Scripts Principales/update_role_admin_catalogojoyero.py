#!/usr/bin/env python3
# Script: update_role_admin_catalogojoyero.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 update_role_admin_catalogojoyero.py [opciones]
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
db = client['app_catalogojoyero']
users = db['users']

result = users.update_one({'username': 'edefrutos'}, {'$set': {'role': 'admin'}})
if result.modified_count == 1:
    print("✅ Rol actualizado a admin para 'edefrutos' en 'app_catalogojoyero'")
else:
    print("⚠️ No se actualizó ningún usuario en 'app_catalogojoyero'. ¿Ya era admin o no existe?") 