# Script: test_mongo_connection.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo_connection.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-03

import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener la URI de MongoDB
MONGO_URI = os.getenv('MONGO_URI')

try:
    # Intentar conectar
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    # Verificar conexión
    client.admin.command('ping')
    print("Conexión exitosa a MongoDB")
    
    # Listar bases de datos
    print("Bases de datos disponibles:")
    for db in client.list_database_names():
        print(f"- {db}")
    
except Exception as e:
    print(f"Error al conectar a MongoDB: {str(e)}")
