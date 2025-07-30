#!/usr/bin/env python3

# Script: show_admin_user.py
# Descripción: [Localizar usuario administrador, previamente identificado en el script]
# Uso: python3 show_admin_user.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-05

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from app.models import get_users_collection

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
db_name = os.getenv("MONGODB_DB", "app_catalogojoyero_nueva")
COLLECTION = "users"

client = MongoClient(MONGO_URI)
db = client[db_name]
users = get_users_collection()

admin = users.find_one({"email": "edfrutos@gmail.com"})

if admin:
    print("Usuario edfrutos@gmail.com:")
    for k, v in admin.items():
        print(f"  {k}: {v}")
else:
    print("No se encontró el usuario edfrutos@gmail.com")
