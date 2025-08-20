#!/usr/bin/env python3
# Script: check_user.py
# Descripción: Comprobar el rol de usuario
# Uso: python3 check_user_role.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

import os

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

from app.models import get_users_collection

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client: MongoClient = MongoClient(os.getenv("MONGO_URI"))
db = client["app_catalogojoyero_nueva"]
users_collection = get_users_collection()

try:
    # Buscar el usuario por email
    user = users_collection.find_one({"email": "edfrutos@gmail.com"})

    if user:
        print(f"Usuario encontrado: {user['email']}")
        print(f"Rol actual: {user.get('role', 'No tiene rol')}")

        # Actualizar el rol a admin
        result = users_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"role": "admin"}}
        )

        if result.modified_count > 0:
            print("Rol actualizado a admin")
        else:
            print("No se pudo actualizar el rol")
    else:
        print("Usuario no encontrado")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    client.close()
