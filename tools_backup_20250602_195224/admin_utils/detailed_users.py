#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv
from pprint import pprint
from app.models import get_users_collection

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['app_catalogojoyero_nueva']
users_collection = get_users_collection()
spreadsheets_collection = db['spreadsheets']

def print_user_details(user):
    print(f"\nUsuario: {user.get('username')}")
    print(f"Email: {user.get('email')}")
    print(f"Rol: {user.get('role', 'No especificado')}")
    print(f"Fecha de registro: {user.get('created_at', 'No especificada')}")
    print(f"Última actualización: {user.get('updated_at', 'No especificada')}")
    print("Documento completo del usuario:")
    pprint(user)

# 1. Usuarios sin rol específico
print("\n=== Usuarios sin Rol Específico ===")
users_no_role = list(users_collection.find({"$or": [{"role": {"$exists": False}}, {"role": None}]}))
print(f"Total de usuarios sin rol: {len(users_no_role)}")
for user in users_no_role:
    print_user_details(user)
    # Buscar tablas del usuario
    if user.get('username'):
        tables = list(spreadsheets_collection.find({"owner": user.get('username')}))
        if tables:
            print(f"\nTablas asociadas a {user.get('username')}:")
            for table in tables:
                print(f"- {table.get('name')} (ID: {table.get('_id')})")
                print(f"  Creada: {table.get('created_at')}")
                print(f"  Archivo: {table.get('filename')}")

# 2. Información detallada de Felipe
print("\n=== Información Detallada de Felipe ===")
felipe_user = users_collection.find_one({"$or": [{"username": "Felipe"}, {"email": "felipe@gmail.com"}]})
if felipe_user:
    print_user_details(felipe_user)

print("\nTablas de Felipe:")
felipe_tables = list(spreadsheets_collection.find({"owner": "Felipe"}))
for table in felipe_tables:
    print("\nDetalles de la tabla:")
    pprint(table)
    # Verificar si el archivo existe
    if table.get('filename'):
        filepath = os.path.join("/spreadsheets", table.get('filename'))
        print(f"¿Archivo existe?: {os.path.exists(filepath)}")

# 3. Buscar información sobre Julia
print("\n=== Información sobre Julia ===")
julia_user = users_collection.find_one({"$or": [{"username": "Julia"}, {"email": {"$regex": "julia", "$options": "i"}}]})
if julia_user:
    print_user_details(julia_user)
else:
    print("No se encontró usuario registrado para Julia")

print("\nHistorial de Tablas de Julia:")
julia_tables = list(spreadsheets_collection.find({"owner": "Julia"}))
print(f"Total de tablas encontradas: {len(julia_tables)}")
for table in julia_tables:
    print("\nDetalles de la tabla:")
    pprint(table)

# 4. Resumen general de usuarios y sus tablas
print("\n=== Resumen General de Usuarios y sus Tablas ===")
all_tables = list(spreadsheets_collection.find())
user_tables = {}
for table in all_tables:
    owner = table.get('owner')
    if owner not in user_tables:
        user_tables[owner] = []
    user_tables[owner].append({
        'name': table.get('name'),
        'id': table.get('_id'),
        'created_at': table.get('created_at'),
        'filename': table.get('filename')
    })

for owner, tables in user_tables.items():
    print(f"\nPropietario: {owner}")
    user = users_collection.find_one({"$or": [{"username": owner}, {"_id": owner}]})
    if user:
        print(f"Email: {user.get('email')}")
        print(f"Rol: {user.get('role', 'No especificado')}")
    print(f"Número de tablas: {len(tables)}")
    for table in tables:
        print(f"- {table['name']} (ID: {table['id']}, Creada: {table['created_at']})")
