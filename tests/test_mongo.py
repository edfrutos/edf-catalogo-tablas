# Script: test_mongo.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from dotenv import load_dotenv
import os
from pymongo import MongoClient
import certifi

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("Error: MONGO_URI no está definida")
    exit(1)

# Intentar conexión
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    # Probar conexión
    client.admin.command('ping')
    print("Conexión exitosa a MongoDB")
    
    # Listar bases de datos disponibles
    print("Bases de datos disponibles:")
    print(client.list_database_names())
    
    db = client["app_catalogojoyero_nueva"]
    print("Colecciones disponibles:", db.list_collection_names())
    print("Usuarios:", db["users"].count_documents({}))
    print("Catálogos:", db["catalogos"].count_documents({}))
    print("Spreadsheets:", db["spreadsheets"].count_documents({}))
    
except Exception as e:
    print(f"Error al conectar a MongoDB: {str(e)}")
