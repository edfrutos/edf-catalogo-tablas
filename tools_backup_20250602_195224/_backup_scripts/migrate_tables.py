#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi
from datetime import datetime

def migrate_tables():
    # Cargar variables de entorno
    load_dotenv()
    MONGO_URI = os.getenv('MONGO_URI')
    
    # Conectar a MongoDB
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        retryWrites=True,
        w='majority'
    )
    db = client['app_catalogojoyero_nueva']
    
    # Obtener colecciones
    tables_collection = db['67b8c24a7fdc72dd4d8703cf']
    users_collection = db['users']
    
    # Mapeo de tablas conocidas a usuarios
    table_owners = {
        'joyero.xlsx': 'j.g.1991@hotmail.es',  # Julia
        'tabla.xlsx': 'edfrutos@gmail.com',     # edefrutos
    }
    
    # Obtener todas las tablas únicas
    unique_tables = tables_collection.distinct('table')
    print(f"Encontradas {len(unique_tables)} tablas únicas")
    
    for table_name in unique_tables:
        if not table_name:
            continue
            
        # Obtener el propietario de la tabla
        owner_email = table_owners.get(table_name)
        if owner_email:
            # Buscar información del usuario
            user = users_collection.find_one({"email": owner_email})
            if user:
                # Preparar información del propietario
                owner_info = {
                    "owner_email": user.get("email"),
                    "owner_name": user.get("nombre"),
                    "owner_username": user.get("username"),
                    "created_at": datetime.now(),
                    "created_by": user.get("email")
                }
                
                # Actualizar todos los registros de esta tabla
                result = tables_collection.update_many(
                    {"table": table_name},
                    {"$set": owner_info}
                )
                print(f"Tabla {table_name}: actualizados {result.modified_count} registros")
            else:
                print(f"Usuario no encontrado para el email: {owner_email}")
        else:
            print(f"Propietario no especificado para la tabla: {table_name}")
    
    print("Migración completada")

if __name__ == "__main__":
    migrate_tables()
