#!/usr/bin/env python3
# Script: test_mongo_ssl.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo_ssl.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

print("Probando conexión a MongoDB Atlas con verificación SSL...")

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    dbs = client.list_database_names()
    print("✅ Conexión exitosa. Bases de datos disponibles:")
    for db in dbs:
        print(" -", db)
except Exception as e:
    print("❌ Error de conexión:")
    print(e)
    print("\nSugerencias:")
    print("- Verifica que la URI es correcta y accesible.")
    print("- Asegúrate de tener certifi actualizado: pip install --upgrade certifi")
    print("- Si usas Mac, ejecuta el instalador de certificados de Python.") 