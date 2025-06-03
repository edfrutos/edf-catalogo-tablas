#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

# Cargar variables de entorno
load_dotenv()

# Usar la URI de Atlas desde el entorno
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('No se encontró la variable de entorno MONGO_URI')

# Usar el certificado de certifi para evitar errores SSL
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["app_catalogojoyero_nueva"]

# Usar la colección principal de catálogos/tablas
collection = db["spreadsheets"]

# Insertar un documento de prueba
# Puedes personalizar los campos según la estructura real
import datetime
test_doc = {
    "name": "Catálogo de Prueba",
    "headers": ["Columna1", "Columna2"],
    "rows": [{"Columna1": "Valor1", "Columna2": "Valor2"}],
    "created_by": "script_test",
    "owner": "script_test",
    "owner_name": "Script Test",
    "email": "script@test.com",
    "created_at": datetime.datetime.utcnow(),
    "updated_at": datetime.datetime.utcnow()
}
collection.insert_one(test_doc)

# Comprobar si el documento se insertó
print("Documento insertado:", collection.find_one({"name": "Catálogo de Prueba"}))