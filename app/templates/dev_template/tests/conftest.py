# Script: conftest.py
# Configuración de fixtures globales para pytest en proyectos Flask/MongoDB

import pytest
import sys
import os
from dotenv import load_dotenv
import certifi
from unittest.mock import MagicMock

# Añadir la raíz del proyecto al sys.path para que se pueda importar app.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))

# Cargar variables de entorno del .env antes de crear la app
load_dotenv()

from app import create_app
from app.database import initialize_db, get_mongo_client, get_mongo_db

@pytest.fixture(scope="session")
def mongo_client_ssl():
    """Cliente MongoDB robusto para integración, forzando TLS 1.2 y bundle certifi."""
    mongo_uri = os.getenv('MONGO_URI')
    from pymongo import MongoClient
    client = MongoClient(
        mongo_uri,
        tls=True,
        tlsCAFile=certifi.where()
    )
    try:
        client.admin.command("ping")
    except Exception as e:
        print(f"[DEBUG pytest] Error en ping a MongoDB: {e}")
    yield client
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
    return user

@pytest.fixture
def app():
    """Fixture para crear la aplicación Flask de prueba."""
    return create_app(testing=True)

@pytest.fixture
def client(app):
    """Fixture para obtener un test client de Flask."""
    return app.test_client()
