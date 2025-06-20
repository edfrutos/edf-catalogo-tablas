#!/usr/bin/env python3
# Script: insert_admin_and_minimum_data.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 insert_admin_and_minimum_data.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import certifi
import hashlib
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
db = client['app_catalogojoyero_nueva']  # Usar base de datos explícita

def scrypt_hash_password(password):
    salt = secrets.token_hex(8)
    hashed = hashlib.scrypt(password.encode('utf-8'), salt=salt.encode('utf-8'), n=32768, r=8, p=1, dklen=64)
    return f"scrypt:32768:8:1${salt}${hashed.hex()}"

import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Inserta un usuario admin en app_catalogojoyero_nueva")
    parser.add_argument('--username', help='Nombre de usuario')
    parser.add_argument('--email', help='Email del usuario')
    parser.add_argument('--password', help='Contraseña del usuario')
    parser.add_argument('--role', default='admin', help='Rol (por defecto: admin)')
    parser.add_argument('--json', action='store_true', help='Salida en formato JSON')
    args = parser.parse_args()

    # Pedir datos por input si no se pasan por argumento
    username = args.username or input('Username: ')
    email = args.email or input('Email: ')
    password = args.password or input('Password: ')
    role = args.role or input('Role [admin]: ') or 'admin'

    admin_user = {
        "username": username,
        "email": email,
        "password": scrypt_hash_password(password),
        "role": role,
        "active": True
    }
    exists = db.users.find_one({"username": username})
    result = {}
    if exists:
        msg = f"Usuario '{username}' ya existe. No se insertó."
        result = {"success": False, "msg": msg}
        print(msg)
    else:
        db.users.insert_one(admin_user)
        msg = f"Usuario '{username}' insertado correctamente."
        result = {"success": True, "msg": msg, "user": {k: v for k, v in admin_user.items() if k != 'password'}}
        print(msg)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()

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