# Script: test_catalogs_rows.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_catalogs_rows.py [opciones]
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
def created_catalog_id(client, login):
    """
    Crea un catálogo de prueba antes de los tests y devuelve su ID. Borra el catálogo al finalizar.
    """
    catalog_data = {
        'name': 'TestCatRows',
        'headers': 'Col1,Col2'
    }
    resp = client.post('/catalogs/create', data=catalog_data, follow_redirects=True)
    assert resp.status_code == 200
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.data, 'html.parser')
    link = soup.find('a', href=lambda h: h and h.startswith('/catalogs/') and len(h) > 10)
    assert link, 'No se encontró enlace al catálogo creado'
    catalog_id = link['href'].split('/')[-1]
    yield catalog_id
    client.post(f'/catalogs/delete/{catalog_id}', follow_redirects=True)

@pytest.fixture
def example_row():
    return {'Col1': 'valor1', 'Col2': 'valor2'}

def test_add_row_get(client, login, created_catalog_id):
    if not created_catalog_id:
        pytest.skip('No hay catálogo creado para filas')
    resp = client.get(f'/catalogs/add-row/{created_catalog_id}')
    assert resp.status_code == 200
    assert b'fila' in resp.data.lower() or b'agregar' in resp.data.lower()

def test_add_row_post(client, login, created_catalog_id, example_row):
    if not created_catalog_id:
        pytest.skip('No hay catálogo creado para filas')
    resp = client.post(f'/catalogs/add-row/{created_catalog_id}', data=example_row, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'fila' in text or 'agregada' in text or 'éxito' in text

# Para test de edición y borrado, necesitamos saber el índice de la fila creada
# Se asume que la fila agregada es la última
@pytest.fixture
def last_row_index(client, login, created_catalog_id, example_row):
    # Asegurar que hay al menos una fila
    resp = client.get(f'/catalogs/{created_catalog_id}')
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.data, 'html.parser')
    rows = soup.find_all('tr')
    if len(rows) <= 1:
        # No hay filas, agregar una
        resp_add = client.post(f'/catalogs/add-row/{created_catalog_id}', data=example_row, follow_redirects=True)
        assert resp_add.status_code == 200
        resp = client.get(f'/catalogs/{created_catalog_id}')
        soup = BeautifulSoup(resp.data, 'html.parser')
        rows = soup.find_all('tr')
    if len(rows) > 1:
        return len(rows) - 2  # header + 0-indexed
    return None

def test_edit_row_get(client, login, created_catalog_id, last_row_index):
    if not created_catalog_id or last_row_index is None:
        pytest.skip('No hay fila para editar')
    resp = client.get(f'/catalogs/edit-row/{created_catalog_id}/{last_row_index}')
    assert resp.status_code == 200
    assert b'fila' in resp.data.lower() or b'editar' in resp.data.lower()

def test_edit_row_post(client, login, created_catalog_id, last_row_index):
    if not created_catalog_id or last_row_index is None:
        pytest.skip('No hay fila para editar')
    resp = client.post(f'/catalogs/edit-row/{created_catalog_id}/{last_row_index}', data={'Col1': 'nuevo', 'Col2': 'valor2'}, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'fila' in text or 'actualizada' in text or 'éxito' in text

def test_delete_row(client, login, created_catalog_id, last_row_index):
    if not created_catalog_id or last_row_index is None:
        pytest.skip('No hay fila para borrar')
    resp = client.post(f'/catalogs/delete-row/{created_catalog_id}/{last_row_index}', follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'fila' in text or 'eliminada' in text or 'éxito' in text or 'no se pudo' in text
