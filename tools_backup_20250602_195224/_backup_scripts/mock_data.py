#!/usr/bin/env python3
# Script para generar datos de prueba cuando MongoDB no está disponible
# Creado: 17/05/2025

import os
import sys
import json
from flask import Flask, g

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = []
    
    def find(self, query=None, **kwargs):
        return self.data
    
    def find_one(self, query=None, **kwargs):
        if self.data:
            return self.data[0]
        return None
    
    def insert_one(self, document):
        self.data.append(document)
        return True
    
    def update_one(self, query, update, **kwargs):
        return True
    
    def delete_one(self, query):
        return True
    
    def count_documents(self, query=None):
        return len(self.data)

class MockDB:
    def __init__(self):
        self.spreadsheets = MockCollection("spreadsheets")
        self.catalogs = MockCollection("catalogs")
        self.users = MockCollection("users")
        
        # Añadir algunos datos de prueba
        self.users.data = [
            {"_id": "admin_id", "username": "admin", "email": "admin@example.com", "role": "admin"},
            {"_id": "user_id", "username": "usuario", "email": "usuario@example.com", "role": "user"}
        ]
        
        self.spreadsheets.data = [
            {"_id": "table1", "filename": "tabla_ejemplo.xlsx", "name": "Tabla de Ejemplo", "headers": ["ID", "Nombre", "Descripción"]}
        ]
        
        self.catalogs.data = [
            {"_id": "catalog1", "name": "Catálogo de Prueba", "description": "Un catálogo para pruebas", "rows": []}
        ]

class MockPyMongo:
    def __init__(self, app=None):
        self.db = MockDB()

def patch_app(app):
    """Parcha la aplicación Flask para usar datos simulados en lugar de MongoDB"""
    app.mock_mongo = MockPyMongo()
    
    # Reemplazar las colecciones con versiones simuladas
    if not hasattr(app, 'spreadsheets_collection') or app.spreadsheets_collection is None:
        app.spreadsheets_collection = app.mock_mongo.db.spreadsheets
    
    if not hasattr(app, 'catalogs_collection') or app.catalogs_collection is None:
        app.catalogs_collection = app.mock_mongo.db.catalogs
    
    if not hasattr(app, 'users_collection') or app.users_collection is None:
        app.users_collection = app.mock_mongo.db.users
    
    print("Aplicación parchada para usar datos simulados en lugar de MongoDB")
    return app

# Función para ser importada desde otros scripts
def get_mock_mongo():
    return MockPyMongo()

if __name__ == "__main__":
    print("Este script debe ser importado desde app.py, no ejecutado directamente")
    sys.exit(1)
