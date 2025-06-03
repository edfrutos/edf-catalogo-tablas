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

# Buscar todas las tablas de Julia
tablas_julia = list(spreadsheets_collection.find({"owner": "Julia"}))

print("\n=== Tablas de Julia ===")
print(f"Total de tablas encontradas: {len(tablas_julia)}")
for tabla in tablas_julia:
    print("\nDetalles de la tabla:")
    print(f"ID: {tabla.get('_id')} (tipo: {type(tabla.get('_id'))})")
    print(f"Nombre: {tabla.get('name')}")
    print(f"Filename: {tabla.get('filename')}")
    print(f"Created at: {tabla.get('created_at')}")
    print(f"Owner: {tabla.get('owner')}")
    print(f"Headers: {tabla.get('headers')}")
    print("Documento completo:", tabla)

# Verificar si los archivos existen
SPREADSHEET_FOLDER = "/spreadsheets"
print("\n=== Verificación de archivos ===")
for tabla in tablas_julia:
    filename = tabla.get('filename')
    if filename:
        filepath = os.path.join(SPREADSHEET_FOLDER, filename)
        print(f"\nArchivo: {filename}")
        print(f"Ruta completa: {filepath}")
        print(f"¿Existe el archivo?: {os.path.exists(filepath)}")
