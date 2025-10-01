#!/usr/bin/env python3
from pymongo import MongoClient
import os

import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
try:
    client: MongoClient = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
    print(client.admin.command("ping"))
except Exception as e:
    print(f"Error: {e}")
