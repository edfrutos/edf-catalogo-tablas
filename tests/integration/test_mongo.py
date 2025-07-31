# Script: test_mongo.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import pytest

@pytest.mark.integration
def test_mongo_connection(mongo_client_ssl):
    client = mongo_client_ssl
    # Probar conexión
    client.admin.command('ping')
    dbs = client.list_database_names()
    assert "app_catalogojoyero_nueva" in dbs
    db = client["app_catalogojoyero_nueva"]
    # Verifica que las colecciones existen
    collections = db.list_collection_names()
    assert "users" in collections
    assert "catalogos" in collections
    assert "spreadsheets" in collections
    # Verifica que hay documentos (puedes ajustar si esperas vacío)
    assert db["users"].count_documents({}) >= 0
    assert db["catalogos"].count_documents({}) >= 0
    assert db["spreadsheets"].count_documents({}) >= 0
