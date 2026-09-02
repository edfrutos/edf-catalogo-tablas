#!/usr/bin/env python3
from pymongo import MongoClient
import os

import certifi
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()

uri = os.environ.get("MONGO_URI")
if not uri:
    raise SystemExit("Define MONGO_URI en el archivo .env antes de ejecutar este script")
try:
    client: MongoClient = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
    print(client.admin.command("ping"))
except Exception as e:
    print(f"Error: {e}")
