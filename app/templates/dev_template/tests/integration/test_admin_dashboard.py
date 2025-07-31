import pytest
from flask import url_for

# Asume que hay un fixture 'client' y 'app' disponible (como en otros tests)

def login_admin(client):
    resp = client.post('/login', data={
        'email': 'edfrutos@gmail.com',
        'password': 'scrypt:32768:8:1$LEYiEVQl50ED9xjD$bf91f7fce83e7e57ac953b373aef401673126799d84820439d2b138b759960319d16a50e7f995d05ee9d7d1d3f15548e75f21cbf3684b25c812721672b8ab1a1',
    }, follow_redirects=True)
    assert b'logout' in resp.data.lower() or b'panel' in resp.data.lower()
    return resp

def test_admin_dashboard_access(client, app):
    """El dashboard de admin debe ser accesible para admin logueado."""
    force_admin_session(client, app)
    resp = client.get('/admin/')
    assert resp.status_code == 200
    assert b'Panel' in resp.data or b'Admin' in resp.data

def test_admin_db_scripts_access(client, app):
    """La vista de scripts de BD debe requerir admin y responder 200."""
    force_admin_session(client, app)
    resp = client.get('/admin/db-scripts')
    assert resp.status_code == 200
    assert b'Script' in resp.data or b'BD' in resp.data or b'Database' in resp.data

def test_admin_db_performance_access(client, app):
    """La vista de performance DB debe requerir admin y responder 200."""
    force_admin_session(client, app)
    resp = client.get('/admin/db/performance')
    assert resp.status_code == 200
    assert b'Pruebas' in resp.data or b'Performance' in resp.data or b'Rendimiento' in resp.data or b'Database' in resp.data

import flask

def force_admin_session(client, app):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'admin'
        sess['email'] = 'edfrutos@gmail.com'
        sess['username'] = 'edefrutos'
        sess['user_id'] = 'testid123'
        # Clave especial para Flask-Login
        sess['_user_id'] = 'edfrutos@gmail.com'
        sess['is_admin'] = True
    # Fijar la cookie de sesión llamando a una ruta dummy
    client.get('/')


def test_admin_logs_manual_access(client, app):
    """La vista manual de logs debe requerir admin y responder 200."""
    force_admin_session(client, app)
    resp = client.get('/admin/logs')
    assert resp.status_code == 200
    assert b'Log' in resp.data or b'Logs' in resp.data


def test_admin_logs_tail_json(client, app):
    """La API de tail logs debe devolver JSON y status 200 o error controlado."""
    force_admin_session(client, app)
    resp = client.get('/admin/logs/tail?log_file=flask_debug.log&n=2')
    assert resp.status_code in (200, 404, 500)
    assert resp.is_json
    data = resp.get_json()
    assert 'logs' in data


def test_admin_logs_clear(client, app):
    """La API de clear logs debe devolver JSON y status 200 o 404."""
    force_admin_session(client, app)
    resp = client.post('/admin/logs/clear?log_file=flask_debug.log')
    assert resp.status_code in (200, 404)
    assert resp.is_json
    data = resp.get_json()
    assert 'status' in data
