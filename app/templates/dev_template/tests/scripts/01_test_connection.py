# Script: 01_test_connection.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 01_test_connection.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-03

from pymongo import MongoClient
import os

import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

# URI de conexión a MongoDB Atlas
uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"

try:
    # Crear cliente de MongoDB
    client = MongoClient(uri, tlsCAFile=certifi.where())
    # Probar conexión
    print("Conexión exitosa a MongoDB Atlas")
    # Listar bases de datos
    print("Bases de datos disponibles:", client.list_database_names())
except Exception as e:
    print("Error al conectar a MongoDB Atlas:", e)
