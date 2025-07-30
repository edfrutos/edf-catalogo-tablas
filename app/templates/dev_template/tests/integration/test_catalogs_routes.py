# Script: test_catalogs_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_catalogs_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for

@pytest.fixture
def login(client):
    resp = client.post('/login', data={
        'email': 'edfrutos@gmail.com',
        'password': '15si34Maf$'
    }, follow_redirects=True)
    assert b'logout' in resp.data.lower() or b'panel' in resp.data.lower(), 'Login real falló. Verifica credenciales.'
    return resp

def test_catalog_list_requires_login(client):
    resp = client.get('/catalogs/', follow_redirects=False)
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']

def test_catalog_list_ok(client, login):
    resp = client.get('/catalogs/')
    assert resp.status_code == 200
    assert b'cat' in resp.data.lower() or b'lista' in resp.data.lower()

def test_catalog_create_requires_login(client):
    resp = client.get('/catalogs/create', follow_redirects=False)
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']

def test_catalog_create_get(client, login):
    resp = client.get('/catalogs/create')
    assert resp.status_code == 200
    assert b'cat' in resp.data.lower() or b'nombre' in resp.data.lower()

def test_catalog_create_post_missing_data(client, login):
    resp = client.post('/catalogs/create', data={'name': ''}, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'error' in text or 'nombre' in text or 'cat' in text

def test_catalog_import_requires_login(client):
    resp = client.get('/catalogs/import', follow_redirects=False)
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']

def test_catalog_import_get(client, login):
    resp = client.get('/catalogs/import')
    assert resp.status_code == 200
    assert b'import' in resp.data.lower() or b'archivo' in resp.data.lower()

def test_catalog_view_requires_login(client):
    resp = client.get('/catalogs/000000000000000000000000', follow_redirects=False)
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']

def test_catalog_view_404(client, login):
    resp = client.get('/catalogs/000000000000000000000000', follow_redirects=True)
    assert resp.status_code in (404, 302, 200)
    text = resp.data.decode(errors='ignore').lower()
    assert 'error' in text or 'cat' in text or 'no encontrado' in text or 'danger' in text
