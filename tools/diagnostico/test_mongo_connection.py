#!/usr/bin/env python3
# Script: test_mongo_connection.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo_connection.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import certifi

# Cargar variables de entorno
load_dotenv()

# Obtener la URI desde el entorno
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('No se encontró la variable de entorno MONGO_URI')

client: MongoClient = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
)

try:
    client.admin.command('ping')
    print('¡Conexión exitosa a MongoDB Atlas!')
except Exception as e:
    print('Error de conexión:', e) 