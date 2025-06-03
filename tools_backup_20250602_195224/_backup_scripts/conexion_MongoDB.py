#!/usr/bin/env python3
from pymongo import MongoClient

uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
try:
    client = MongoClient(uri, tls=True)
    print(client.admin.command('ping'))
except Exception as e:
    print(f"Error: {e}")