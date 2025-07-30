# Archivo movido a tests/legacy/. Conservar solo si es necesario.
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_session_routes_test.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest

def test_session_home(client):
    resp = client.get('/test_session/')
    assert resp.status_code == 200
    assert b'test_timestamp' in resp.data or b'session' in resp.data


def test_session_check(client):
    # Primero accedemos a la home para crear la variable de sesión
    client.get('/test_session/')
    resp = client.get('/test_session/check', follow_redirects=True)
    assert resp.status_code == 200
    assert b'prueba persiste' in resp.data or b'sesi' in resp.data


def test_session_api(client):
    client.get('/test_session/')
    resp = client.get('/test_session/api/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['session_active'] is True
    assert 'test_timestamp' in data


def test_session_reset(client):
    client.get('/test_session/')
    resp = client.get('/test_session/reset', follow_redirects=True)
    assert resp.status_code == 200
    assert b'eliminado' in resp.data or b'sesi' in resp.data
