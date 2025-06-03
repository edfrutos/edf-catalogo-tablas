#!/usr/bin/env python3
import os
from pymongo import MongoClient
from app.models import get_users_collection

# Cargar variables de entorno si es necesario
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DBNAME', 'app_catalogojoyero_nueva')
COLLECTION = 'users'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = get_users_collection()

updated = 0
for user in users.find({}):
    update_fields = {}
    if 'role' not in user:
        update_fields['role'] = 'user'
    if 'username' not in user and 'nombre' in user:
        update_fields['username'] = user['nombre']
    if 'email' not in user and 'email' in user:
        update_fields['email'] = user['email']
    if update_fields:
        users.update_one({'_id': user['_id']}, {'$set': update_fields})
        updated += 1

print(f"Usuarios actualizados: {updated}") 