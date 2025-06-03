#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
import certifi

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'), tlsCAFile=certifi.where())
db = client['app_catalogojoyero_nueva']
users_collection = db['users']
spreadsheets_collection = db['spreadsheets']

def print_separator():
    print("\n" + "="*50 + "\n")

# 1. Eliminar usuarios sospechosos
print("=== Eliminando Usuarios Sospechosos ===")
suspicious_ids = [
    ObjectId('67efefdaa5363dd9379c2859'),  # ricardo@gmail.com
    ObjectId('67f3c2e9a5363dd9379c285b')   # floydlipu1992@gmail.com
]

result = users_collection.delete_many({'_id': {'$in': suspicious_ids}})
print(f"Usuarios eliminados: {result.deleted_count}")

print_separator()

# 2. Verificar rol de Julia
print("=== Verificando Rol de Julia ===")
julia = users_collection.find_one({"email": "j.g.1991@hotmail.es"})
if julia:
    print("Información de Julia:")
    print(f"Email: {julia.get('email')}")
    print(f"Nombre: {julia.get('nombre')}")
    print(f"Rol: {julia.get('role')}")
    print(f"Última actualización: {julia.get('updated_at')}")
else:
    print("¡Error! No se encontró el usuario de Julia")

print_separator()

# 3. Limpieza general
print("=== Limpieza General ===")

# 3.1 Verificar archivos físicos vs registros en BD
print("\nVerificando archivos físicos vs registros en BD:")
SPREADSHEET_FOLDER = "/spreadsheets"
all_tables = list(spreadsheets_collection.find())

print("\nArchivos sin registro en BD:")
physical_files = set(f for f in os.listdir(SPREADSHEET_FOLDER) if f.endswith(('.xlsx', '.xls', '.csv')))
db_files = set(table['filename'] for table in all_tables if table.get('filename'))
orphan_files = physical_files - db_files
for file in orphan_files:
    print(f"- {file}")
    filepath = os.path.join(SPREADSHEET_FOLDER, file)
    os.remove(filepath)
    print(f"  ¡Eliminado!")

print("\nRegistros sin archivo físico:")
missing_files = []
for table in all_tables:
    if table.get('filename'):
        filepath = os.path.join(SPREADSHEET_FOLDER, table['filename'])
        if not os.path.exists(filepath):
            print(f"- Tabla: {table.get('name')} (ID: {table.get('_id')})")
            print(f"  Propietario: {table.get('owner')}")
            print(f"  Archivo: {table.get('filename')}")
            missing_files.append(table.get('_id'))

if missing_files:
    result = spreadsheets_collection.delete_many({'_id': {'$in': missing_files}})
    print(f"\nRegistros sin archivo físico eliminados: {result.deleted_count}")

# 3.2 Verificar usuarios sin email o con email duplicado
print("\nVerificando usuarios sin email o con email duplicado:")
all_users = list(users_collection.find())
emails = {}
for user in all_users:
    email = user.get('email')
    if not email:
        print(f"Usuario sin email (ID: {user.get('_id')})")
    else:
        if email in emails:
            print(f"Email duplicado: {email}")
            print(f"- Usuario 1: {emails[email]}")
            print(f"- Usuario 2: {user.get('_id')}")
        else:
            emails[email] = user.get('_id')

print_separator()

# Resumen final
print("=== Resumen de Limpieza ===")
print("1. Usuarios sospechosos eliminados")
print("2. Rol de Julia verificado")
print(f"3. Archivos huérfanos eliminados: {len(orphan_files)}")
print(f"4. Registros sin archivo físico eliminados: {len(missing_files)}")

# Estado actual de la base de datos
print("\nEstado actual de la base de datos:")
print(f"Total de usuarios: {users_collection.count_documents({})}")
print(f"Total de tablas: {spreadsheets_collection.count_documents({})}")

print("\n¡Limpieza completada!")
