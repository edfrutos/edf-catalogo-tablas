#!/usr/bin/env python3
import os
import re
from datetime import datetime

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'), tlsCAFile=certifi.where())
db = client['app_catalogojoyero_nueva']
users_collection = db['users']
spreadsheets_collection = db['spreadsheets']

def is_random_name(name):
    # Patrones que sugieren nombres aleatorios
    patterns = [
        r'^[A-Z]{2,}$',  # Todas mayúsculas
        r'[0-9]{4,}',    # Muchos números seguidos
        r'[A-Z]{3,}[a-z]{3,}[A-Z]{3,}',  # Mezcla inusual de mayúsculas/minúsculas
        r'^[a-zA-Z0-9]{10,}$'  # Cadenas largas sin espacios
    ]
    return any(re.search(pattern, name) for pattern in patterns)

# 1. Asignar rol normal a Julia
print("\n=== Asignando rol normal a Julia ===")
result = users_collection.update_one(
    {"email": "j.g.1991@hotmail.es"},
    {"$set": {"role": "normal", "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
)
print(f"Actualización de Julia: {result.modified_count} documento(s) modificado(s)")

# 2. Limpiar tabla de Felipe
print("\n=== Limpiando tabla de Felipe ===")
felipe_table = spreadsheets_collection.find_one({"owner": "Felipe"})
if felipe_table:
    print(f"Eliminando tabla: {felipe_table.get('name')}")
    result = spreadsheets_collection.delete_one({"_id": felipe_table.get('_id')})
    print(f"Eliminación de tabla: {result.deleted_count} documento(s) eliminado(s)")

# 3. Investigar usuarios sospechosos
print("\n=== Investigando usuarios con nombres aleatorios ===")
all_users = list(users_collection.find())
suspicious_users = []

for user in all_users:
    nombre = user.get('nombre', '')
    if nombre and is_random_name(nombre):
        print("\nUsuario sospechoso encontrado:")
        print(f"Email: {user.get('email')}")
        print(f"Nombre: {nombre}")
        print(f"ID: {user.get('_id')}")
        print(f"Fecha de registro: {user.get('created_at', 'No especificada')}")

        # Verificar si tiene tablas
        tables = list(spreadsheets_collection.find({"owner": user.get('username', '')}))
        if tables:
            print(f"Tablas asociadas: {len(tables)}")
            for table in tables:
                print(f"- {table.get('name')} (Creada: {table.get('created_at')})")
        else:
            print("No tiene tablas asociadas")

        suspicious_users.append(user.get('_id'))

print(f"\nTotal de usuarios sospechosos encontrados: {len(suspicious_users)}")

# Mostrar resumen final
print("\n=== Resumen de Acciones ===")
print("1. Rol de Julia actualizado a 'normal'")
print("2. Tabla de Felipe sin archivo físico eliminada")
print(f"3. {len(suspicious_users)} usuarios sospechosos identificados")

# Sugerir acciones
print("\n=== Acciones Sugeridas ===")
if suspicious_users:
    print("Para los usuarios sospechosos, se sugiere:")
    print("1. Verificar la legitimidad de sus correos electrónicos")
    print("2. Revisar sus patrones de uso")
    print("3. Considerar su eliminación si no tienen actividad legítima")
    print("\nPara eliminar estos usuarios, ejecute un nuevo script con:")
    print("users_collection.delete_many({'_id': {'$in': suspicious_users}})")
