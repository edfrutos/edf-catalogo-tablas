#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

try:
    # Conexión a MongoDB usando la URI del archivo .env
    print("Conectando a MongoDB...")
    client = MongoClient(os.getenv('MONGO_URI'))
    
    # Verificar conexión
    client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB")
    
    # Usar la base de datos correcta
    db = client['app_catalogojoyero_nueva']
    
    # Buscar la tabla específica que no se puede eliminar
    table_id = "67d9ad1d66dcc288b664da32"  # ID de la tabla problemática
    table = db.spreadsheets.find_one({"_id": ObjectId(table_id)})
    
    if table:
        print("\nDetalles de la tabla problemática:")
        print(f"ID: {table.get('_id')}")
        print(f"Filename: {table.get('filename')}")
        print(f"Owner: {table.get('owner')}")
        print(f"Nombre: {table.get('name')}")
        print(f"Headers: {table.get('headers')}")
        print(f"Fecha de creación: {table.get('created_at')}")
        print("\nContenido completo del documento:")
        print(table)
        
        # Verificar si el archivo existe en el sistema
        file_path = os.path.join('spreadsheets', table.get('filename', ''))
        print(f"\n¿Existe el archivo físico? {os.path.exists(file_path)}")
        if os.path.exists(file_path):
            print(f"Ruta del archivo: {file_path}")
            print(f"Tamaño del archivo: {os.path.getsize(file_path)} bytes")
    else:
        print("\nNo se encontró la tabla en la base de datos.")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
