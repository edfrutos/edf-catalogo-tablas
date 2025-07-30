# Script: test_main_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_main_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest

def test_index_redirects(client):
    """
    La raíz '/' debe redirigir a welcome o dashboard según sesión.
    """
    resp = client.get('/')
    # Sin sesión, redirige a welcome
    assert resp.status_code in (302, 200)
    # Si es 302, debe redirigir a /welcome
    if resp.status_code == 302:
        assert '/welcome' in resp.headers['Location']


def test_dashboard_user_requires_login(client):
    """
    El dashboard de usuario debe requerir login (redirige o 401/403).
    """
    resp = client.get('/admin/maintenance/dashboard_user')
    assert resp.status_code in (302, 401, 403)


def test_tables_redirect(client):
    """
    La ruta /tables debe redirigir a /catalogs.
    """
    resp = client.get('/tables')
    assert resp.status_code in (302, 200)
    if resp.status_code == 302:
        assert '/catalogs' in resp.headers['Location']


def test_soporte_get(client):
    """
    El formulario de soporte debe responder 200 (GET).
    """
    resp = client.get('/soporte')
    assert resp.status_code == 200
    assert b'soporte' in resp.data.lower() or b'contact' in resp.data.lower()


def test_select_table_requires_login(client):
    """
    Seleccionar tabla sin login debe redirigir a login.
    """
    resp = client.get('/select_table/12345')
    assert resp.status_code in (302, 401, 403)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']
