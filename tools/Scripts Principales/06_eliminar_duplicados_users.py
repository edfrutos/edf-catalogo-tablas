#!/usr/bin/env python3
# Script: 06_eliminar_duplicados_users.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 06_eliminar_duplicados_users.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient
from collections import defaultdict

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- ELIMINACIÓN AUTOMÁTICA DE USUARIOS DUPLICADOS ---')

users = list(db['users'].find())

deleted_ids = set()

# Eliminar duplicados por email
email_map = defaultdict(list)
for u in users:
    email = u.get('email','').lower()
    if email:
        email_map[email].append(u)

for email, us in email_map.items():
    if len(us) > 1:
        # Mantener el primero, eliminar el resto
        to_keep = us[0]['_id']
        for u in us[1:]:
            db['users'].delete_one({'_id': u['_id']})
            deleted_ids.add(str(u['_id']))
        print(f"✔ Eliminados {len(us)-1} usuarios duplicados con email '{email}' (se mantiene _id: {to_keep})")

# Eliminar duplicados por username (de los que quedan)
users = list(db['users'].find())
username_map = defaultdict(list)
for u in users:
    username = u.get('username','').lower()
    if username:
        username_map[username].append(u)

for username, us in username_map.items():
    if len(us) > 1:
        to_keep = us[0]['_id']
        for u in us[1:]:
            db['users'].delete_one({'_id': u['_id']})
            deleted_ids.add(str(u['_id']))
        print(f"✔ Eliminados {len(us)-1} usuarios duplicados con username '{username}' (se mantiene _id: {to_keep})")

if deleted_ids:
    print(f"\nResumen: eliminados {len(deleted_ids)} usuarios duplicados en total.")
else:
    print("No se encontraron usuarios duplicados para eliminar.")

print('--- FIN DE LA ELIMINACIÓN AUTOMÁTICA ---') 