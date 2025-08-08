#!/usr/bin/env python3
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash
import datetime
from typing import Optional

load_dotenv()
uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGODB_DB", "app_catalogojoyero_nueva")
client: MongoClient = MongoClient(uri, tls=True)
db = client[db_name]
users = db["users"]

# Verificar si ya existe el usuario admin
if users.count_documents({}) == 0:
    print("Inicializando base de datos con usuario admin...")

    # Crear usuario admin
    admin_data = {
        "nombre": "Admin",
        "email": "admin@example.com",
        "password": generate_password_hash(
            "admin123"
        ),  # Usar método por defecto pbkdf2:sha256
        "role": "admin",
        "num_tables": 0,
        "tables_updated_at": datetime.datetime.utcnow(),
        "last_ip": "",
        "last_login": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "failed_attempts": 0,
        "locked_until": None,
    }

    result = users.insert_one(admin_data)
    print(f"Usuario admin creado con éxito. ID: {result.inserted_id}")

    # Verificar que el usuario se creó correctamente
    admin_user = users.find_one({"email": "admin@example.com"})
    if admin_user:
        print("\nDatos del usuario admin creado:")
        print(f"Nombre: {admin_user['nombre']}")
        print(f"Email: {admin_user['email']}")
        print(f"Rol: {admin_user['role']}")
    else:
        print("Error: No se pudo verificar el usuario creado")
else:
    print("La base de datos ya tiene usuarios registrados")
