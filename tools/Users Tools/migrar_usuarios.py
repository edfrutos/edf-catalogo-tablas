# Script: migrar_usuarios.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 migrar_usuarios.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from pymongo import MongoClient
import certifi
import os
from werkzeug.security import generate_password_hash
import secrets

client = MongoClient(os.getenv('MONGO_URI'), tlsCAFile=certifi.where())
db = client.get_database()

users_col = db['users']
usuarios_col = db['usuarios']
users_unified_col = db['users_unified']

# Función para comprobar si un usuario ya existe en 'users'
def usuario_existe(email, username):
    return users_col.find_one({"$or": [{"email": email}, {"username": username}]}) is not None

# Contraseña temporal segura
def generar_password_temporal():
    return secrets.token_urlsafe(12)

# Migrar usuarios de 'usuarios'
usuarios = list(usuarios_col.find())
for u in usuarios:
    email = u.get('email')
    username = u.get('username') or u.get('nombre') or u.get('name')
    if not email or not username:
        continue
    if usuario_existe(email, username):
        continue
    password_temp = generar_password_temporal()
    user_doc = {
        "username": username,
        "email": email,
        "role": u.get('role') or u.get('rol', 'user'),
        "name": u.get('name') or u.get('nombre', username),
        "password": generate_password_hash(password_temp),
        "must_change_password": True,
        "migrated_from": "usuarios"
    }
    users_col.insert_one(user_doc)
    print(f"Migrado usuario de 'usuarios': {email} (contraseña temporal: {password_temp})")

# Migrar usuarios de 'users_unified'
usuarios_unificados = list(users_unified_col.find())
for u in usuarios_unificados:
    email = u.get('email')
    username = u.get('username') or u.get('nombre') or u.get('name')
    if not email or not username:
        continue
    if usuario_existe(email, username):
        continue
    password_temp = generar_password_temporal()
    user_doc = {
        "username": username,
        "email": email,
        "role": u.get('role', 'user'),
        "name": u.get('name') or u.get('nombre', username),
        "password": generate_password_hash(password_temp),
        "must_change_password": True,
        "migrated_from": "users_unified"
    }
    users_col.insert_one(user_doc)
    print(f"Migrado usuario de 'users_unified': {email} (contraseña temporal: {password_temp})")

print("Migración completada.") 