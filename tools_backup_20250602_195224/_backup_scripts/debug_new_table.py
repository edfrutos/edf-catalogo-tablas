#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['app_catalogojoyero_nueva']
spreadsheets_collection = db['spreadsheets']

# Buscar la tabla específica de Julia creada hoy
today = datetime.now().strftime("%Y-%m-%d")
tabla = spreadsheets_collection.find_one({
    "owner": "Julia",
    "name": "Joyero",
    "created_at": {"$regex": f"^{today}"}
})

if tabla:
    print("\n=== Detalles de la tabla ===")
    print(f"ID: {tabla.get('_id')} (tipo: {type(tabla.get('_id'))})")
    print(f"Nombre: {tabla.get('name')}")
    print(f"Filename: {tabla.get('filename')}")
    print(f"Created at: {tabla.get('created_at')}")
    print(f"Owner: {tabla.get('owner')}")
    print(f"Headers: {tabla.get('headers')}")
    print("\nDocumento completo:", tabla)

    # Verificar si el archivo existe
    SPREADSHEET_FOLDER = "/spreadsheets"
    filename = tabla.get('filename')
    if filename:
        filepath = os.path.join(SPREADSHEET_FOLDER, filename)
        print(f"\nVerificación del archivo:")
        print(f"Ruta completa: {filepath}")
        print(f"¿Existe el archivo?: {os.path.exists(filepath)}")
        if os.path.exists(filepath):
            print(f"Permisos del archivo: {oct(os.stat(filepath).st_mode)[-3:]}")
else:
    print("No se encontró la tabla")
