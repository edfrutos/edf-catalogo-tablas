#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: mock_data.py
Descripción: Proporciona datos simulados cuando MongoDB no está disponible
Uso: Importar las funciones necesarias
Autor: Eugenio de Frutos - 2025
"""

import os
import json
from datetime import datetime

def get_mock_mongo():
    """
    Retorna un objeto que simula la conexión a MongoDB para pruebas
    """
    class MockDB:
        def __init__(self):
            self.collections = {}
            self._initialize_mock_data()

        def _initialize_mock_data(self):
            """Inicializa datos de prueba básicos"""
            self.collections = {
                'users': [],
                'catalogs': [],
                'sessions': []
            }

    return MockDB()

def patch_app(app):
    """
    Modifica la aplicación Flask para usar datos simulados
    
    Args:
        app: Instancia de Flask app
        
    Returns:
        app: Aplicación modificada para usar datos simulados
    """
    # Configurar la app para usar datos simulados
    app.config['TESTING'] = True
    app.config['MOCK_DATA'] = True
    
    # Crear conexión simulada
    mock_db = get_mock_mongo()
    
    # Inyectar la conexión simulada en la app
    app.mongo = mock_db
    
    return app

def get_mock_data(collection_name):
    """
    Retorna datos simulados para una colección específica
    
    Args:
        collection_name: Nombre de la colección
        
    Returns:
        list: Lista de documentos simulados
    """
    mock_data = {
        'users': [
            {
                '_id': '1',
                'username': 'admin',
                'email': 'admin@example.com',
                'role': 'admin',
                'created_at': datetime.now()
            }
        ],
        'catalogs': [
            {
                '_id': '1',
                'name': 'Catálogo de Prueba',
                'owner': '1',
                'created_at': datetime.now(),
                'rows': []
            }
        ]
    }
    
    return mock_data.get(collection_name, [])

if __name__ == '__main__':
    print("Este script está diseñado para ser importado, no ejecutado directamente.")
