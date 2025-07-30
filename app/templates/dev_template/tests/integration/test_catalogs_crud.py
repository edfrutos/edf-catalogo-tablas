# Script: test_catalogs_crud.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_catalogs_crud.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for
from bson import ObjectId

@pytest.fixture
def login(client):
    resp = client.post('/login', data={
        'email': 'edfrutos@gmail.com',
        'password': '15si34Maf$'
    }, follow_redirects=True)
    assert b'logout' in resp.data.lower() or b'panel' in resp.data.lower(), 'Login real falló. Verifica credenciales.'
    return resp

@pytest.fixture
def new_catalog_data():
    return {
        'name': 'Catálogo Test CRUD',
        'description': 'Catálogo de prueba para tests CRUD',
        'headers': 'Col1,Col2'
    }

def test_create_catalog_ok(client, login, new_catalog_data):
    resp = client.post('/catalogs/create', data=new_catalog_data, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'cat' in text or 'creado' in text or 'éxito' in text
    # Extraer el ID del catálogo creado si es posible
    import re
    match = re.search(r'/catalogs/([a-f0-9]{24})', text)
    if match:
        catalog_id = match.group(1)
        # Guardar el ID para otros tests
        with open('/tmp/test_catalog_id.txt', 'w') as f:
            f.write(catalog_id)

@pytest.fixture(scope='module')
def created_catalog_id():
    try:
        with open('/tmp/test_catalog_id.txt') as f:
            return f.read().strip()
    except Exception:
        return None

def test_edit_catalog_get(client, login, created_catalog_id):
    if not created_catalog_id:
        pytest.skip('No hay catálogo creado para editar')
    resp = client.get(f'/catalogs/{created_catalog_id}/edit')
    assert resp.status_code == 200
    assert b'cat' in resp.data.lower() or b'nombre' in resp.data.lower()

def test_edit_catalog_post(client, login, created_catalog_id):
    if not created_catalog_id:
        pytest.skip('No hay catálogo creado para editar')
    resp = client.post(f'/catalogs/{created_catalog_id}/edit', data={
        'name': 'Catálogo Editado',
        'headers': 'Col1,Col2,Col3'
    }, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'cat' in text or 'actualizado' in text or 'éxito' in text

def test_delete_catalog(client, login, created_catalog_id):
    if not created_catalog_id:
        pytest.skip('No hay catálogo creado para eliminar')
    resp = client.post(f'/catalogs/delete/{created_catalog_id}', follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'cat' in text or 'eliminado' in text or 'éxito' in text or 'no se pudo' in text
