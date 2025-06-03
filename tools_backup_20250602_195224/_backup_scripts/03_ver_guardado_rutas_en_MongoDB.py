#!/usr/bin/env python3
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["app_catalogojoyero_nueva"]
collection = db["spreadsheets"]

for doc in collection.find():
    print(doc)