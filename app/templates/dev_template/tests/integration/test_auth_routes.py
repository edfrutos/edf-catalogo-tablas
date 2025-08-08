# Script: test_auth_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_auth_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from datetime import datetime

LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
DEBUG_SECRET_URL = '/debug_secret_key'

ADMIN_USER = {
    'username': 'edefrutos',
    'email': 'edfrutos@gmail.com',
    'password': '15si34Maf$',
    'role': 'admin'
}

@pytest.fixture(autouse=True)
def ensure_admin_user(app):
    """Asegura que el usuario admin de test existe en la base de datos antes de cada test."""
    with app.app_context():
        mongo = getattr(app, 'mongo', None)
        if mongo is None:
            pytest.skip('MongoDB no inicializado en app')
        users = mongo.db.users
        # Elimina cualquier usuario duplicado antes de insertar
        users.delete_many({
            '$or': [
                {'username': 'edefrutos'},
                {'email': 'edfrutos@gmail.com'}
            ]
        })
        users.insert_one({
            'username': 'edefrutos',
            'email': 'edfrutos@gmail.com',
            'password': 'scrypt:32768:8:1$LEYiEVQl50ED9xjD$bf91f7fce83e7e57ac953b373aef401673126799d84820439d2b138b759960319d16a50e7f995d05ee9d7d1d3f15548e75f21cbf3684b25c812721672b8ab1a1',
            'role': 'admin',
            'active': True,
            'failed_attempts': 0,
            'last_ip': '127.0.0.1',
            'last_login': datetime.utcnow().isoformat(),
            'locked_until': None,
            'verified': True,
            'nombre': 'edefrutos',
            'foto_perfil': 'd1203cc039784d969b8d56450ff66f88_Miguel_Angel_y_yo_de_ninos.jpg',
            '_id': 'testid123'
        })

def test_login_page_loads(client):
    resp = client.get(LOGIN_URL)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'login' in text or 'usuario' in text


def test_login_fail(client):
    resp = client.post(LOGIN_URL, data={'email': 'noexiste@example.com', 'password': 'badpass'}, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'inv' in text or 'error' in text or 'credencial' in text


def test_login_success(client):
    resp = client.post(LOGIN_URL, data={'email': ADMIN_USER['email'], 'password': ADMIN_USER['password']}, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'logout' in text or 'panel' in text or 'admin' in text


def test_logout(client, app):
    # Login primero
    client.post(LOGIN_URL, data={'email': ADMIN_USER['email'], 'password': ADMIN_USER['password']}, follow_redirects=True)
    resp = client.get(LOGOUT_URL, follow_redirects=True)
    assert resp.status_code == 200
    text = resp.data.decode(errors='ignore').lower()
    assert 'login' in text or 'sesión' in text or 'has cerrado' in text


def test_debug_secret_key_requires_login(client):
    resp = client.get(DEBUG_SECRET_URL)
    assert resp.status_code in (401, 302)
    if resp.status_code == 302:
        assert '/login' in resp.headers['Location']


def test_debug_secret_key_success(client, app):
    # Login primero
    client.post(LOGIN_URL, data={'email': ADMIN_USER['email'], 'password': ADMIN_USER['password']}, follow_redirects=True)
    resp = client.get(DEBUG_SECRET_URL)
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert 'SECRET_KEY' in data
