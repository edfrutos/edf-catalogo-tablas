# Script: create_test_user.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 create_test_user.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client["app_catalogojoyero_nueva"]
users = db["users"]

# Datos del usuario de prueba
test_user = {
    "nombre": "Test User",
    "email": "test@example.com",
    "password": generate_password_hash("test123"),
    "created_at": datetime.utcnow(),
    "role": "user",
    "updated_at": datetime.utcnow().isoformat(),
    "failed_attempts": 0,
    "last_ip": "",
    "last_login": None,
    "locked_until": None,
    "num_tables": 0,
    "password_updated_at": datetime.utcnow().isoformat(),
    "tables_updated_at": None
}

# Datos del usuario normal
user_normal = {
    "nombre": "Usuario Normal",
    "username": "usuario_normal",
    "email": "usuario@example.com",
    "password": generate_password_hash("usuario123"),
    "created_at": datetime.utcnow(),
    "role": "user",
    "updated_at": datetime.utcnow().isoformat(),
    "failed_attempts": 0,
    "last_ip": "",
    "last_login": None,
    "locked_until": None,
    "num_tables": 0,
    "password_updated_at": datetime.utcnow().isoformat(),
    "tables_updated_at": None
}

# Verificar y crear usuario de prueba
existing_user = users.find_one({"email": "test@example.com"})
if existing_user:
    print("El usuario de prueba ya existe")
else:
    # Crear el usuario
    result = users.insert_one(test_user)
    print(f"Usuario de prueba creado con ID: {result.inserted_id}")

# Verificar y crear usuario normal
existing_normal = users.find_one({"email": "usuario@example.com"})
if existing_normal:
    print("El usuario normal ya existe")
else:
    # Crear el usuario normal
    result = users.insert_one(user_normal)
    print(f"Usuario normal creado con ID: {result.inserted_id}")

# Verificar que podemos recuperar los usuarios
user = users.find_one({"email": "test@example.com"})
if user:
    print(f"Usuario test encontrado: {user['email']}")
    print(f"Rol: {user['role']}")
else:
    print("No se pudo encontrar el usuario test")
    
user_normal_check = users.find_one({"email": "usuario@example.com"})
if user_normal_check:
    print(f"Usuario normal encontrado: {user_normal_check['email']}")
    print(f"Rol: {user_normal_check['role']}")
else:
    print("No se pudo encontrar el usuario normal")
