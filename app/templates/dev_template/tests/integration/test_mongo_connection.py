# Script: test_mongo_connection.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_mongo_connection.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-03

import pytest

@pytest.mark.integration
def test_mongo_connection_basic(mongo_client_ssl):
    client = mongo_client_ssl
    # Verificar conexión
    client.admin.command('ping')
    dbs = client.list_database_names()
    assert isinstance(dbs, list)
    assert len(dbs) > 0
    assert any(isinstance(db, str) for db in dbs)
