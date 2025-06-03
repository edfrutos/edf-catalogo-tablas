#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

load_dotenv()

os.environ['SSL_CERT_FILE'] = certifi.where()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

# Conectar directamente a MongoDB usando la URL de conexión
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/edf_catalogotablas')
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
db = client.get_database()

print('Estructura de un documento en catalogs:')
catalogs = list(db.catalogs.find().limit(1))
if catalogs:
    print(list(catalogs[0].keys()))
    # Verificar si hay imágenes en los datos
    if 'data' in catalogs[0] and catalogs[0]['data']:
        for i, row in enumerate(catalogs[0]['data']):
            if 'imagenes' in row or 'images' in row:
                print(f"Fila {i} tiene imágenes: {'imagenes' in row}, {'images' in row}")
                if 'imagenes' in row:
                    print(f"Ejemplo de imagen: {row['imagenes'][0] if row['imagenes'] else 'vacío'}")
                if 'images' in row:
                    print(f"Ejemplo de imagen: {row['images'][0] if row['images'] else 'vacío'}")
                break
else:
    print('No hay documentos en catalogs')

print('\nEstructura de un documento en spreadsheets:')
spreadsheets = list(db.spreadsheets.find().limit(1))
if spreadsheets:
    print(list(spreadsheets[0].keys()))
    # Verificar si hay imágenes en los datos
    if 'data' in spreadsheets[0] and spreadsheets[0]['data']:
        for i, row in enumerate(spreadsheets[0]['data']):
            if 'imagenes' in row or 'images' in row:
                print(f"Fila {i} tiene imágenes: {'imagenes' in row}, {'images' in row}")
                if 'imagenes' in row:
                    print(f"Ejemplo de imagen: {row['imagenes'][0] if row['imagenes'] else 'vacío'}")
                if 'images' in row:
                    print(f"Ejemplo de imagen: {row['images'][0] if row['images'] else 'vacío'}")
                break
else:
    print('No hay documentos en spreadsheets')
