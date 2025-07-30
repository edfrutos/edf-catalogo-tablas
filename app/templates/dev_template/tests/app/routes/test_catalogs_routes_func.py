# Script: test_catalogs_routes_func.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_catalogs_routes_func.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for

def test_catalogs_list_redirect(client):
    resp = client.get("/catalogs/", follow_redirects=True)
    # Puede redirigir a login si no autenticado
    assert resp.status_code in (200, 302)

def test_import_catalog_get(client):
    resp = client.get("/catalogs/import", follow_redirects=True)
    assert resp.status_code in (200, 302)
    # Puede contener palabra 'importar' o 'cat\xe1logo'
    assert b"import" in resp.data.lower() or b"cat\xe1logo" in resp.data.lower()
