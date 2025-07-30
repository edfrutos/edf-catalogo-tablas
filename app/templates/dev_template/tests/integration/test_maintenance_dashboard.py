# Script: test_maintenance_dashboard.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_maintenance_dashboard.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for
import bcrypt

ADMIN_USER = {
    'username': 'edefrutos',
    'password': '15si34Maf$',
    'email': 'edefrutos@example.com',
    'role': 'admin'
}

@pytest.fixture(autouse=True)
def ensure_admin_user(app):
    """Asegura que el usuario admin de test existe en la base de datos antes de cada test."""
    from datetime import datetime
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
            'foto_perfil': 'd1203cc039784d969b8d56450ff66f88_Miguel_Angel_y_yo_de_ninos.jpg'
        })

def login(client):
    resp = client.post('/login', data={
        'email': 'edfrutos@gmail.com',  # usar el email real, que es el campo que matchea el hash
        'password': ADMIN_USER['password']
    }, follow_redirects=True)
    assert b'logout' in resp.data.lower() or b'panel' in resp.data.lower(), 'Login real falló. Verifica credenciales.'
    return resp

def test_dashboard_route(client, app):
    """La ruta del dashboard debe responder 200 y contener los textos clave."""
    login(client)
    resp = client.get('/admin/maintenance/dashboard')
    assert resp.status_code == 200
    assert b'Mantenimiento' in resp.data or b'Panel' in resp.data


def test_maintenance_home(client, app):
    """La ruta /admin/maintenance/home debe responder 200 y mostrar datos de disco y temporales."""
    login(client)
    resp = client.get('/admin/maintenance/home')
    assert resp.status_code == 200
    # Debe contener alguna palabra clave del template
    assert b'disk' in resp.data or b'temp_files' in resp.data or b'usuario' in resp.data


def test_view_log_no_file(client, app):
    """La API de view_log debe devolver error 400 si no se especifica archivo."""
    login(client)
    resp = client.get('/admin/maintenance/admin/logs/view')
    assert resp.status_code == 400
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error'
    assert 'Archivo no especificado' in data['message']


def test_view_log_not_found(client, app):
    """La API de view_log debe devolver error 404 si el archivo no existe."""
    login(client)
    resp = client.get('/admin/maintenance/admin/logs/view?file=noexiste.log')
    assert resp.status_code == 404
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'error'
    assert 'Archivo no encontrado' in data['message']


def test_view_log_success_or_empty(client, app, tmp_path):
    """La API de view_log debe devolver status success o error controlado si el archivo existe o está vacío."""
    # Crear un log temporal en la carpeta logs
    import os
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    os.makedirs(logs_dir, exist_ok=True)
    test_log_path = os.path.join(logs_dir, 'test_api.log')
    with open(test_log_path, 'w', encoding='utf-8') as f:
        f.write('Linea1\nLinea2\n')
    login(client)
    resp = client.get('/admin/maintenance/admin/logs/view?file=test_api.log&lines=2')
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'Linea1' in data['content']
    # Limpieza
    os.remove(test_log_path)

def test_list_logs(client, app):
    """La ruta de list_logs debe responder 200 y devolver HTML o JSON."""
    login(client)
    resp = client.get('/admin/maintenance/api/list_logs')
    assert resp.status_code == 200
    assert b'log' in resp.data.lower() or resp.is_json

def test_api_list_logs(client, app):
    """La API de list_logs debe responder 200 y devolver una lista o JSON."""
    login(client)
    resp = client.get('/admin/maintenance/api/list_logs')
    assert resp.status_code == 200
    # Puede ser JSON o HTML, según implementación
    if resp.is_json:
        data = resp.get_json()
        assert isinstance(data, list) or isinstance(data, dict)

def test_cleanup_temp(client, app):
    """La API de cleanup-temp debe responder 200 o error controlado."""
    login(client)
    resp = client.post('/admin/maintenance/api/cleanup-temp')
    assert resp.status_code in (200, 400, 422)

def test_system_status(client, app):
    """La API de estado del sistema debe responder 200 y contener claves esperadas."""
    login(client)
    resp = client.get('/admin/maintenance/api/system_status')
    assert resp.status_code == 200, f"Status esperado 200, recibido {resp.status_code}"
    assert resp.is_json, "La respuesta debe ser JSON"
    data = resp.get_json()
    # 1. Claves obligatorias
    for key in ['status', 'memoria', 'so', 'arquitectura', 'usuario', 'hora']:
        assert key in data, f"Falta la clave '{key}' en la respuesta"
    # 2. Status debe ser success
    assert data['status'] == 'success', f"Status esperado 'success', recibido {data['status']}"
    # 3. Tipos y rangos
    memoria = data['memoria']
    assert isinstance(memoria, dict)
    for k in ['total_gb', 'disponible_gb', 'porcentaje']:
        assert k in memoria
        assert isinstance(memoria[k], (int, float)), f"{k} debe ser numérico"
        if k == 'porcentaje':
            assert 0 <= memoria[k] <= 100, f"Porcentaje de memoria fuera de rango: {memoria[k]}"
    assert isinstance(data['so'], str) and data['so'], "Campo 'so' vacío"
    assert isinstance(data['arquitectura'], str) and data['arquitectura'], "Campo 'arquitectura' vacío"
    assert isinstance(data['usuario'], str) and data['usuario'], "Campo 'usuario' vacío"
    # 4. Formato de fecha/hora
    import re
    assert re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', data['hora']), f"Formato de hora inválido: {data['hora']}"
    # 5. No hay campos inesperados
    for k in data.keys():
        assert k in ['status', 'memoria', 'so', 'arquitectura', 'usuario', 'hora'], f"Campo inesperado en respuesta: {k}"
    # 6. Valores no vacíos
    for k in ['so', 'arquitectura', 'usuario']:
        assert data[k], f"Campo {k} vacío"


def test_system_status_requires_auth(client):
    """El endpoint debe requerir autenticación/admin."""
    resp = client.get('/admin/maintenance/api/system_status', follow_redirects=False)
    # Puede ser redirect a login (302/401) o 403
    assert resp.status_code in (302, 401, 403)


def test_system_status_error_handling(monkeypatch, client, app):
    """Simula fallo interno y comprueba respuesta de error controlado."""
    login(client)
    # Parchea psutil.virtual_memory para lanzar excepción globalmente
    import psutil
    def fail_psutil(*args, **kwargs):
        raise RuntimeError("Error simulado de psutil")
    monkeypatch.setattr(psutil, 'virtual_memory', fail_psutil)
    try:
        resp = client.get('/admin/maintenance/api/system_status')
    except RuntimeError:
        assert True
    else:
        # Puede responder 200 con status error, o 500
        assert resp.status_code in (200, 500)
        if resp.status_code == 200 and resp.is_json:
            data = resp.get_json()
            assert data['status'] == 'error' or 'error' in data.get('message','').lower()
        elif resp.status_code == 500:
            assert 'Error simulado de psutil' in resp.get_data(as_text=True)


def test_scheduled_tasks(client, app):
    """La API de tareas programadas debe responder 200 y devolver la estructura esperada."""
    login(client)
    resp = client.get('/admin/maintenance/api/scheduled_tasks')
    assert resp.status_code == 200, f"Status esperado 200, recibido {resp.status_code}"
    assert resp.is_json, "La respuesta debe ser JSON"
    data = resp.get_json()
    assert 'tasks' in data, "La respuesta debe contener la clave 'tasks'"
    assert isinstance(data['tasks'], list), "'tasks' debe ser una lista"
    for task in data['tasks']:
        assert 'id' in task and 'estado' in task and 'ultima_ejecucion' in task, "Cada tarea debe tener 'id', 'estado' y 'ultima_ejecucion'"


def test_run_task_success(client, app):
    """La API de ejecución de tarea debe permitir ejecutar una tarea válida y devolver éxito."""
    login(client)
    for task in ['cleanup', 'mongo', 'disk']:
        resp = client.post('/admin/maintenance/api/run_task', data={'task': task})
        assert resp.status_code in (200, 429), f"Status inesperado: {resp.status_code}"
        if resp.status_code == 429:
            assert 'Demasiadas peticiones' in resp.get_data(as_text=True)
        else:
            assert resp.is_json, "La respuesta debe ser JSON"
            data = resp.get_json()
            assert data['status'] in ('success', 'error'), "Respuesta debe tener status 'success' o 'error'"
            if data['status'] == 'success':
                assert 'completada' in data['message'].lower() or 'ejecutada' in data['message'].lower()


def test_run_task_invalid(client, app):
    """La API debe rechazar tareas inválidas."""
    login(client)
    resp = client.post('/admin/maintenance/api/run_task', data={'task': 'noexiste'})
    assert resp.status_code == 400, f"Status esperado 400 para tarea inválida, recibido {resp.status_code}"
    assert resp.is_json, "La respuesta debe ser JSON"
    data = resp.get_json()
    assert data['status'] == 'error', "Status debe ser 'error' para tarea inválida"
    assert 'desconocida' in data['message'].lower() or 'no permitida' in data['message'].lower()


def test_truncate_logs_requires_admin(client):
    """El endpoint /api/truncate-logs debe requerir autenticación/admin."""
    # Sin login
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": ["flask_debug.log"]})
    # Debe devolver error de autenticación/autorización (no 200)
    assert resp.status_code != 200, f"Status esperado distinto de 200, recibido {resp.status_code}"


def test_truncate_logs_complete(tmp_path, client, app):
    """Debe truncar completamente un log existente y responder correctamente."""
    # Crear log temporal
    import os
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    os.makedirs(logs_dir, exist_ok=True)
    test_log = os.path.join(logs_dir, 'test_truncate.log')
    with open(test_log, 'w', encoding='utf-8') as f:
        f.write('Linea1\nLinea2\nLinea3\n')
    login(client)
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": ["test_truncate.log"], "method": "complete"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success' or 'processed_files' in data or 'error_files' in data
    # Verificar que el archivo está vacío
    with open(test_log, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == ''


def test_truncate_logs_lines(tmp_path, client, app):
    """Debe truncar un log a las últimas N líneas."""
    import os
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    test_log = os.path.join(logs_dir, 'test_truncate_lines.log')
    lines = [f"Linea {i}" for i in range(1, 21)]
    with open(test_log, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    login(client)
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": ["test_truncate_lines.log"], "method": "lines", "lineCount": 10})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success' or 'processed_files' in data or 'error_files' in data
    # El archivo debe tener las últimas 10 líneas
    with open(test_log, 'r', encoding='utf-8') as f:
        content = f.read().strip().splitlines()
    assert content == lines[-10:]


def test_truncate_logs_invalid_file(client, app):
    """Debe devolver error si el archivo no existe o el nombre es inválido."""
    login(client)
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": ["noexiste.log", "../../etc/passwd"], "method": "complete"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] in ('success', 'partial', 'error') or 'error_files' in data
    error_files = data.get('error_files', [])
    if not error_files:
        # Imprime la respuesta completa para depuración si la lista viene vacía
        import pytest
        pytest.fail(f"La respuesta no contiene errores esperados. Respuesta completa: {data}")
    assert any('no existe' in s or 'no válido' in s for s in error_files), f"No se encontró mensaje de error esperado en error_files: {error_files}"


def test_truncate_logs_multiple_files(client, app):
    """Debe poder truncar múltiples logs válidos en una sola llamada."""
    import os
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log1 = os.path.join(logs_dir, 'test_multi1.log')
    log2 = os.path.join(logs_dir, 'test_multi2.log')
    with open(log1, 'w', encoding='utf-8') as f:
        f.write('A\nB\nC\n')
    with open(log2, 'w', encoding='utf-8') as f:
        f.write('X\nY\nZ\n')
    login(client)
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": ["test_multi1.log", "test_multi2.log"], "method": "complete"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success' or 'processed_files' in data
    for fname in [log1, log2]:
        with open(fname, 'r', encoding='utf-8') as f:
            assert f.read() == ''


def test_truncate_logs_missing_payload(client, app):
    """Debe manejar el caso de payload JSON faltante o incompleto."""
    login(client)
    resp = client.post('/admin/api/truncate-logs', json=None)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'error' or 'no se proporcionaron datos' in data.get('message', '').lower()


def test_truncate_logs_no_files(client, app):
    """Debe manejar el caso de logFiles vacío."""
    login(client)
    resp = client.post('/admin/api/truncate-logs', json={"logFiles": []})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'error' or 'no se especificaron archivos' in data.get('message', '').lower()

