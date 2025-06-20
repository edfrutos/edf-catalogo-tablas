import pytest

# Utilidad para simular sesión admin (si no existe ya en los fixtures)
def force_admin_session(client, app):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'admin'
        sess['email'] = 'edfrutos@gmail.com'
        sess['username'] = 'edefrutos'
        sess['user_id'] = 'testid123'

# --- TESTS PARA ENDPOINTS ADMIN API ---

def test_api_db_ops_requires_auth(client, app):
    """Debe requerir autenticación y rol admin."""
    resp = client.get('/admin/api/db/ops')
    # Debe rechazar sin sesión admin
    assert resp.status_code in (401, 403)
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False


def test_api_db_ops_success(client, app, admin_user_mock):
    """Debe devolver estadísticas de operaciones si es admin."""
    force_admin_session(client, app)
    resp = client.get('/admin/api/db/ops')
    # Puede fallar si no hay conexión DB, pero debe ser JSON
    assert resp.is_json
    data = resp.get_json()
    assert 'success' in data
    if data['success']:
        assert 'ops_per_sec' in data
        assert 'memory' in data
        assert 'connections' in data
        assert 'timestamp' in data
    else:
        assert 'error' in data


def test_admin_logs_list_requires_auth(client, app):
    resp = client.get('/admin/logs/list')
    assert resp.status_code in (401, 403)
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False


def test_admin_logs_list_success(client, app, admin_user_mock):
    force_admin_session(client, app)
    resp = client.get('/admin/logs/list')
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert 'status' in data and data['status'] == 'success'
    assert 'files' in data
    assert isinstance(data['files'], list)


def test_admin_delete_backups_requires_auth(client, app):
    resp = client.post('/admin/api/delete-backups', json={"files": ["dummy.bak"]})
    assert resp.status_code in (401, 403)
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False


def test_admin_delete_backups_invalid_payload(client, app, admin_user_mock):
    force_admin_session(client, app)
    resp = client.post('/admin/api/delete-backups', json={})
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False


def test_admin_delete_backups_success(client, app, tmp_path, admin_user_mock):
    """Prueba eliminación de backup (mock)."""
    # Crear archivo dummy en carpeta de backups
    import os
    backups_dir = os.path.join(os.getcwd(), 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    test_file = backups_dir + '/test_delete.bak'
    with open(test_file, 'w') as f:
        f.write('dummy')
    force_admin_session(client, app)
    resp = client.post('/admin/api/delete-backups', json={"files": ["test_delete.bak"]})
    assert resp.is_json
    data = resp.get_json()
    assert 'status' in data
    # Limpieza
    if os.path.exists(test_file):
        os.remove(test_file)


def test_admin_backup_upload_to_drive_requires_auth(client, app):
    resp = client.post('/admin/backup/upload-to-drive/test.bak')
    assert resp.status_code in (401, 403)
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False


def test_admin_backup_upload_to_drive_invalid_file(client, app, admin_user_mock):
    force_admin_session(client, app)
    resp = client.post('/admin/backup/upload-to-drive/noexiste.bak')
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error' or data.get('success') is False

# NOTA: No se prueba el caso "success" real de upload-to-drive porque requiere integración con Google Drive y credenciales válidas. Se recomienda mockear la función en tests avanzados.
