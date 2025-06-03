#!/usr/bin/env python3
# checker.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Esto fuerza la conexión
    print("✅ Conexión correcta a MongoDB Atlas")
except Exception as e:
    print(f"❌ Error de conexión a MongoDB: {e}")
