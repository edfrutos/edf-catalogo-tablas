#!/usr/bin/env python3
import certifi
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno desde .env
load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()

uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
try:
    client: MongoClient = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
    print(client.admin.command("ping"))
except Exception as e:
    print(f"Error: {e}")
