#!/usr/bin/env python3
# Script: insert_admin_and_minimum_data.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 insert_admin_and_minimum_data.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import certifi
from scrypt import hash as scrypt_hash
import secrets

# Cargar variables de entorno
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('No se encontró la variable de entorno MONGO_URI')

client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
)
db = client.get_database()  # Usar la base de datos por defecto de la URI

def scrypt_hash_password(password):
    salt = secrets.token_hex(8)
    hashed = scrypt_hash(password.encode('utf-8'), salt.encode('utf-8'), N=32768, r=8, p=1)
    return f"scrypt:32768:8:1${salt}${hashed.hex()}"

# 1. Insertar usuario admin
admin_user = {
    "username": "edefrutos",
    "email": "edefrutos@gmail.com",
    "password": scrypt_hash_password("34Maf15si$"),
    "role": "admin",
    "active": True
}
if not db.users.find_one({"username": "edefrutos"}):
    db.users.insert_one(admin_user)
    print("Usuario edefrutos insertado.")
else:
    print("El usuario edefrutos ya existe.")

# 2. Insertar tabla de ejemplo en spreadsheets
spreadsheet_doc = {
    "name": "Catálogo de Prueba 2",
    "headers": ["Número", "Nombre", "Descripción, Localización, Stock"],
    "filename": "catalogo_prueba_2.xlsx",
    "owner": "edefrutos"
}
if not db.spreadsheets.find_one({"filename": "catalogo_prueba_2.xlsx"}):
    db.spreadsheets.insert_one(spreadsheet_doc)
    print("Tabla de ejemplo insertada en 'spreadsheets'.")
else:
    print("La tabla de ejemplo ya existe en 'spreadsheets'.")

# 3. Insertar registro de ejemplo en catalogs
catalog_doc = {
    "Número": 1,
    "Nombre": "Ejemplo",
    "Descripción": "Primer registro",
    "table": "catalogo_prueba_2.xlsx"
}
if not db.catalogs.find_one({"table": "catalogo_prueba_2.xlsx", "Número": 1}):
    db.catalogs.insert_one(catalog_doc)
    print("Registro de ejemplo insertado en 'catalogs'.")
else:
    print("El registro de ejemplo ya existe en 'catalogs'.") 