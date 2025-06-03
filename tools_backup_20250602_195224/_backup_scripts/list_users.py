#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv
import certifi

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'), tlsCAFile=certifi.where())
db = client['app_catalogojoyero_nueva']
users_collection = db['users']
spreadsheets_collection = db['spreadsheets']

# Obtener todos los usuarios registrados
print("\n=== Usuarios Registrados ===")
users = list(users_collection.find())
print(f"Total de usuarios registrados: {len(users)}")
for user in users:
    print(f"\nUsuario: {user.get('username')}")
    print(f"Email: {user.get('email')}")
    print(f"Rol: {user.get('role', 'No especificado')}")
    # Contar tablas del usuario
    tablas = spreadsheets_collection.count_documents({"owner": user.get('username')})
    print(f"Número de tablas: {tablas}")

# Buscar usuarios únicos en la colección de tablas (por si hay algunos no registrados)
print("\n=== Usuarios con Tablas (incluyendo no registrados) ===")
owners = spreadsheets_collection.distinct("owner")
print(f"Total de usuarios con tablas: {len(owners)}")
for owner in owners:
    tablas = spreadsheets_collection.count_documents({"owner": owner})
    print(f"\nUsuario: {owner}")
    print(f"Número de tablas: {tablas}")
    # Listar las tablas
    print("Tablas:")
    for tabla in spreadsheets_collection.find({"owner": owner}):
        print(f"- {tabla.get('name', 'Sin nombre')} (ID: {tabla.get('_id')})")

print("\n=== BÚSQUEDA DE POSIBLES DUPLICADOS ===")
username = "edefrutos"
email = "edfrutos@gmail.com"
nombre = "edefrutos"

# Buscar por username
users_by_username = list(users_collection.find({"username": username}))
print(f"\nUsuarios con username '{username}': {len(users_by_username)}")
for user in users_by_username:
    print(f"ID: {user.get('_id')}, Email: {user.get('email')}, Rol: {user.get('role')}, Nombre: {user.get('nombre')}")

# Buscar por email
users_by_email = list(users_collection.find({"email": email}))
print(f"\nUsuarios con email '{email}': {len(users_by_email)}")
for user in users_by_email:
    print(f"ID: {user.get('_id')}, Username: {user.get('username')}, Rol: {user.get('role')}, Nombre: {user.get('nombre')}")

# Buscar por nombre
users_by_nombre = list(users_collection.find({"nombre": nombre}))
print(f"\nUsuarios con nombre '{nombre}': {len(users_by_nombre)}")
for user in users_by_nombre:
    print(f"ID: {user.get('_id')}, Username: {user.get('username')}, Email: {user.get('email')}, Rol: {user.get('role')}")
