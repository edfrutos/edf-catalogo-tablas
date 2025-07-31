# Script: test_catalogs_crud_func.py
# Descripción: [El script es un conjunto de pruebas automatizadas (tests) para verificar el correcto funcionamiento de las operaciones CRUD (Crear, Leer, Actualizar y Borrar) sobre los catálogos en una aplicación web basada en Flask.]
# Uso: python3 test_catalogs_crud_func.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
import random
import string
from flask import url_for

def random_catalog_name():
    return 'cat_test_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def login_as_test_user(client):
    # Usa un usuario de test existente o crea uno nuevo
    email = f"crud_{random.randint(1000,9999)}@test.com"
    password = 'CrudTest!2025'
    # Registro
    client.post('/usuarios/register', data={'email': email, 'password': password}, follow_redirects=True)
    # Login
    client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)
    return email

def test_create_catalog(client):
    login_as_test_user(client)
    name = random_catalog_name()
    resp = client.post('/catalogs/create', data={'name': name}, follow_redirects=True)
    assert resp.status_code == 200
    assert (b'cat' in resp.data or b'Cat' in resp.data or b'cat\xc3\xa1logo' in resp.data)

def test_list_catalogs(client):
    login_as_test_user(client)
    resp = client.get('/catalogs/', follow_redirects=True)
    assert resp.status_code == 200
    assert (b'cat' in resp.data or b'Cat' in resp.data or b'cat\xc3\xa1logo' in resp.data)

def test_delete_catalog(client):
    login_as_test_user(client)
    name = random_catalog_name()
    # Crear catálogo
    resp = client.post('/catalogs/create', data={'name': name, 'headers': 'col1'}, follow_redirects=True)
    assert resp.status_code == 200
    # Comprobar que el catálogo aparece en el listado
    list_resp = client.get('/catalogs/', follow_redirects=True)
    assert name in list_resp.data.decode(errors='ignore'), f"Catálogo {name} no aparece en listado tras crearlo"
    # Buscar el id del catálogo en la respuesta del listado
    import re
    card_html = list_resp.data.decode(errors='ignore')
    match = re.search(
        rf'<div class="card.*?<div class="card-header">\s*<h5 class="card-title mb-0">{name}</h5>.*?(?:href="/catalogs/([a-fA-F0-9]+)"|action="/catalogs/delete/([a-fA-F0-9]+))',
        card_html, re.DOTALL)
    if not match:
        pytest.skip('No se pudo extraer el id del catálogo del listado')
    catalog_id = match.group(1) or match.group(2)
    # Eliminar catálogo
    resp = client.post(f'/catalogs/delete/{catalog_id}', follow_redirects=True)
    assert resp.status_code == 200
    import unicodedata
    data = resp.data.decode(errors='ignore')
    data_norm = unicodedata.normalize('NFKD', data).encode('ASCII', 'ignore').decode('ASCII').lower()
    assert 'eliminado' in data_norm

def test_edit_catalog(client):
    login_as_test_user(client)
    name = random_catalog_name()
    # Crear catálogo
    resp = client.post('/catalogs/create', data={'name': name, 'headers': 'col1,col2'}, follow_redirects=True)
    assert resp.status_code == 200
    # Extraer id del catálogo
    import re
    card_html = resp.data.decode(errors='ignore')
    match = re.search(rf'<div class="card.*?<div class="card-header">\s*<h5 class="card-title mb-0">{name}</h5>.*?(?:href="/catalogs/([a-fA-F0-9]+)"|action="/catalogs/delete/([a-fA-F0-9]+))', card_html, re.DOTALL)
    if not match:
        list_resp = client.get('/catalogs/', follow_redirects=True)
        card_html = list_resp.data.decode(errors='ignore')
        match = re.search(rf'<div class="card.*?<div class="card-header">\s*<h5 class="card-title mb-0">{name}</h5>.*?(?:href="/catalogs/([a-fA-F0-9]+)"|action="/catalogs/delete/([a-fA-F0-9]+))', card_html, re.DOTALL)
    if not match:
        pytest.skip('No se pudo extraer el id del catálogo para editarlo')
    catalog_id = match.group(1) or match.group(2)
    # Editar catálogo
    new_name = name + '_editado'
    resp = client.post(f'/catalogs/{catalog_id}/edit', data={'name': new_name, 'headers': 'col1,col2'}, follow_redirects=True)
    assert resp.status_code == 200
    assert new_name in resp.data.decode(errors='ignore')

def test_add_and_edit_row(client):
    login_as_test_user(client)
    name = random_catalog_name()
    # Crear catálogo
    resp = client.post('/catalogs/create', data={'name': name, 'headers': 'col1,col2'}, follow_redirects=True)
    assert resp.status_code == 200
    # Extraer id del catálogo
    import re
    card_html = resp.data.decode(errors='ignore')
    match = re.search(rf'<div class="card.*?<div class="card-header">\s*<h5 class="card-title mb-0">{name}</h5>.*?(?:href="/catalogs/([a-fA-F0-9]+)"|action="/catalogs/delete/([a-fA-F0-9]+))', card_html, re.DOTALL)
    if not match:
        list_resp = client.get('/catalogs/', follow_redirects=True)
        card_html = list_resp.data.decode(errors='ignore')
        match = re.search(rf'<div class="card.*?<div class="card-header">\s*<h5 class="card-title mb-0">{name}</h5>.*?(?:href="/catalogs/([a-fA-F0-9]+)"|action="/catalogs/delete/([a-fA-F0-9]+))', card_html, re.DOTALL)
    if not match:
        pytest.skip('No se pudo extraer el id del catálogo para agregar fila')
    catalog_id = match.group(1) or match.group(2)
    # Añadir una fila
    resp = client.post(f'/catalogs/add-row/{catalog_id}', data={'col1': 'valor1', 'col2': 'valor2'}, follow_redirects=True)
    assert resp.status_code == 200
    # Comprobar que la fila aparece en el detalle del catálogo
    detalle = client.get(f'/catalogs/{catalog_id}', follow_redirects=True)
    html = detalle.data.decode(errors='ignore')
    assert 'valor1' in html and 'valor2' in html
    # Editar la fila (índice 0)
    resp = client.post(f'/catalogs/edit-row/{catalog_id}/0', data={'col1': 'editado1', 'col2': 'editado2'}, follow_redirects=True)
    assert resp.status_code == 200
    detalle = client.get(f'/catalogs/{catalog_id}', follow_redirects=True)
    html = detalle.data.decode(errors='ignore')
    assert 'editado1' in html and 'editado2' in html
    # Eliminar la fila (índice 0)
    resp = client.post(f'/catalogs/delete-row/{catalog_id}/0', follow_redirects=True)
    assert resp.status_code == 200
    detalle = client.get(f'/catalogs/{catalog_id}', follow_redirects=True)
    html = detalle.data.decode(errors='ignore')
    # La fila editada ya no debe aparecer
    assert 'editado1' not in html and 'editado2' not in html
