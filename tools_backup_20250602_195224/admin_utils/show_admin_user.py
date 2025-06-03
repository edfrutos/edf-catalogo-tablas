#!/usr/bin/env python3
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from app.models import get_users_collection
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DBNAME', 'app_catalogojoyero_nueva')
COLLECTION = 'users'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = get_users_collection()

admin = users.find_one({'email': 'admin@example.com'})

if admin:
    print("Usuario admin@example.com:")
    for k, v in admin.items():
        print(f"  {k}: {v}")
else:
    print("No se encontró el usuario admin@example.com") 