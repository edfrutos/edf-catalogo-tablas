# Script: test_mongodb.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongodb.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import pytest
from unittest.mock import MagicMock, patch
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


@pytest.fixture
def mock_mongodb_client():
    """
    Fixture que simula una conexión a MongoDB.
    Retorna un cliente mock con métodos básicos simulados.
    """
    mock_client = MagicMock(spec=MongoClient)
    
    # Simulamos una base de datos y una colección
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Configuramos el comportamiento del mock
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    # Simulamos un comando ping exitoso
    mock_db.command.return_value = {"ok": 1}
    
    return mock_client


@patch('pymongo.MongoClient')
def test_mongodb_connection(mock_mongo_client, mock_mongodb_client):
    """
    Prueba básica para verificar la conexión a MongoDB.
    
    Args:
        mock_mongo_client: Mock de pymongo.MongoClient
        mock_mongodb_client: Fixture que proporciona un cliente MongoDB simulado
    """
    # Configurar el mock para que devuelva nuestro cliente simulado
    mock_mongo_client.return_value = mock_mongodb_client
    
    # Crear una conexión usando el cliente mockeado
    client = MongoClient('mongodb://localhost:27017/')
    
    try:
        # Verificar la conexión
        response = client['admin'].command('ping')
        assert response.get('ok') == 1
        assert "No se pudo conectar a MongoDB" not in str(response)
    except ConnectionFailure:
        pytest.fail("No se pudo conectar a MongoDB")


def test_mongodb_database_access(mock_mongodb_client):
    """
    Prueba el acceso a una base de datos y colección.
    
    Args:
        mock_mongodb_client: Fixture que proporciona un cliente MongoDB simulado
    """
    # Configurar la simulación para que la colección.find() devuelva algunos documentos
    mock_collection = mock_mongodb_client['test_db']['test_collection']
    mock_collection.find.return_value = [
        {"_id": 1, "name": "Documento 1"},
        {"_id": 2, "name": "Documento 2"}
    ]
    
    # Acceder a la base de datos y colección
    db = mock_mongodb_client['test_db']
    collection = db['test_collection']
    
    # Realizar una operación de búsqueda
    results = list(collection.find())
    
    # Verificar que devuelve los documentos esperados
    assert len(results) == 2
    assert results[0]['name'] == "Documento 1"
    assert results[1]['name'] == "Documento 2"

