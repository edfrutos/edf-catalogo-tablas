# Script: conftest.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 conftest.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import os
import sys
from unittest.mock import MagicMock

import certifi
import pytest
from dotenv import load_dotenv

# Añadir la raíz del proyecto al sys.path para que se pueda importar app.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))

# Cargar variables de entorno del .env antes de crear la app
load_dotenv()

from app import create_app
from app.database import get_mongo_client, get_mongo_db, initialize_db


@pytest.fixture(scope="session")
def mongo_client_ssl():
    """Cliente MongoDB robusto para integración, forzando TLS 1.2 y bundle certifi."""
    mongo_uri = os.getenv('MONGO_URI')
    print("[DEBUG pytest] Creando cliente MongoClient...")
    from pymongo import MongoClient
    client = MongoClient(
        mongo_uri,
        tls=True,
        tlsCAFile=certifi.where()
    )
    print("[DEBUG pytest] Cliente MongoClient creado. Intentando ping...")
    try:
        print(client.admin.command("ping"))
    except Exception as e:
        print(f"[DEBUG pytest] Error en ping a MongoDB: {e}")
    yield client
    print("[DEBUG pytest] Cerrando cliente MongoClient...")
    client.close()

@pytest.fixture
def admin_user_mock(monkeypatch):
    """Mock de un usuario administrador para pruebas."""
    user = MagicMock()
    user.is_authenticated = True
    user.is_admin = True
    user.email = "admin@example.com"
    user.username = "edefrutos"
    user.get_id.return_value = "testid123"
    monkeypatch.setattr("flask_login.utils._get_user", lambda: user)
    return user  # Retornar el usuario mock para que esté disponible en los tests


@pytest.fixture
def app():
    """Fixture para crear la aplicación Flask de prueba."""
    print("DEBUG: app fixture ejecutado, create_app path =", create_app.__code__.co_filename)
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Si usas Flask-WTF
    
    # La aplicación ya inicializa MongoDB en create_app(), pero nos aseguramos
    # de que esté correctamente inicializada para los tests
    if not hasattr(app, 'mongo_client') or app.mongo_client is None:
        initialize_db(app=app)
        app.mongo = get_mongo_client()
        app.mongo_db = get_mongo_db()
    
    with app.app_context():
        from flask import g
        g.mongo = app.mongo
        g.users_collection = app.mongo_db["users"]
        yield app  # Usar yield en lugar de return para permitir limpieza después
    
    # No es necesario cerrar el cliente aquí ya que se maneja globalmente,
    # pero podríamos añadir limpieza adicional si fuera necesario

@pytest.fixture
def client(app):
    """Cliente de test para la app Flask."""
    return app.test_client()
