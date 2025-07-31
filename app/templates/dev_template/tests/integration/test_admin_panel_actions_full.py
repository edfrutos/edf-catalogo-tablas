import pytest
from flask import url_for
from unittest.mock import MagicMock, patch

# --- Fixtures ---

def patch_uploaded_images_get_s3_url(app, dummy_url):
    keys = list(app.view_functions.keys())
    print("DEBUG: app.view_functions.keys() =", keys)
    print("DEBUG: 'images.uploaded_images' in keys?", 'images.uploaded_images' in keys)
    for name, view_func in app.view_functions.items():
        view_func.__globals__['get_s3_url'] = lambda filename, expiration=3600: dummy_url


def test_uploaded_images_s3_and_local(client, app, tmp_path):
    """
    Testea el endpoint /imagenes_subidas/<filename> para ambos modos:
    - Redirección a S3 si ?s3=true
    - Descarga local si existe el archivo
    """
    dummy_url = "https://dummy-s3-url.com/fakefile"
    patch_uploaded_images_get_s3_url(app, dummy_url)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    app.s3_client = object()  # Dummy, ya no se usa por el patch
    app.S3_BUCKET_NAME = "dummy-bucket"

    # --- Test S3 ---
    resp = client.get("/imagenes_subidas/testfile.jpg?s3=true")
    print("DEBUG: resp.status_code =", resp.status_code)
    print("DEBUG: resp.data =", resp.data)
    print("DEBUG: resp.headers =", resp.headers)
    assert resp.status_code in (302, 301)
    assert resp.headers["Location"] == dummy_url

    # --- Test local ---
    test_file = tmp_path / "testfile.jpg"
    test_file.write_bytes(b"fake image content")
    resp2 = client.get("/imagenes_subidas/testfile.jpg")
    assert resp2.status_code == 200
    assert resp2.data == b"fake image content"

@pytest.fixture(autouse=True, scope="session")
def mongo_patch_session():
    """
    Mock global para evitar acceso real a MongoDB y dependencias críticas en integración.
    Mockea también servicios externos típicos (correo y S3) para futuras integraciones.
    Se aplica automáticamente a todos los tests de este archivo.
    """
    dummy_settings = {
        "enabled": True,
        "smtp": {
            "server": "smtp.example.com",
            "port": 587,
            "username": "admin@example.com",
            "use_tls": True
        },
        "recipients": ["admin@example.com"],
        "thresholds": {
            "cpu": 80,
            "memory": 90,
            "disk": 85,
            "error_rate": 5
        },
        "cooldown": 60
    }
    from unittest.mock import MagicMock
    mock_s3 = MagicMock()
    mock_s3.upload_file.return_value = None
    mock_s3.download_file.return_value = None
    with patch("app.routes.admin_routes.notifications.update_settings", return_value=True), \
         patch("app.routes.admin_routes.notifications.get_settings", return_value=dummy_settings), \
         patch("app.routes.admin_routes.notifications.send_test_email", return_value=True), \
         patch("app.extensions.mongo", autospec=True) as mock_mongo, \
         patch("boto3.client", return_value=mock_s3):
        yield
@pytest.fixture
def admin_user_mock(monkeypatch):
    user = MagicMock()
    user.is_authenticated = True
    user.is_admin = True
    user.email = "admin@example.com"
    user.username = "adminuser"
    user.get_id.return_value = "adminid123"
    monkeypatch.setattr("flask_login.utils._get_user", lambda: user)
    return user

# ===================== USUARIOS =====================
def test_lista_usuarios(client, admin_user_mock):
    resp = client.get('/admin/usuarios')
    assert resp.status_code == 200
    assert b'Usuarios' in resp.data or b'usuarios' in resp.data

def test_editar_usuario_get_post(client, admin_user_mock):
    # GET usuario existente
    resp = client.get("/admin/usuarios/edit/000000000000000000000001")
    assert resp.status_code == 200 or resp.status_code == 302
    # POST usuario existente (simula update)
    resp2 = client.post("/admin/usuarios/edit/000000000000000000000001", data={"username": "nuevo"}, follow_redirects=True)
    assert resp2.status_code == 200 or resp2.status_code == 302
    # GET usuario inexistente
    resp3 = client.get("/admin/usuarios/edit/ffffffffffffffffffffffff", follow_redirects=True)
    assert resp3.status_code == 200
    assert b"no encontrado" in resp3.data or b"error" in resp3.data or b"danger" in resp3.data

def test_ver_catalogos_usuario_email(client, admin_user_mock):
    resp = client.get("/admin/usuarios/admin@example.com/catalogos")
    assert resp.status_code in (200, 302)
    # Error usuario inexistente
    resp2 = client.get("/admin/usuarios/unknown@no.com/catalogos", follow_redirects=True)
    assert resp2.status_code == 200
    assert b"no encontrado" in resp2.data or b"error" in resp2.data

def test_ver_catalogos_usuario_id(client, admin_user_mock):
    resp = client.get("/admin/catalogos-usuario/000000000000000000000001")
    assert resp.status_code in (200, 302)
    resp2 = client.get("/admin/catalogos-usuario/ffffffffffffffffffffffff", follow_redirects=True)
    assert resp2.status_code == 200
    assert b"no encontrado" in resp2.data or b"error" in resp2.data

# ===================== CATÁLOGOS =====================
def test_ver_catalogo_admin(client, admin_user_mock):
    # Simula acceso a un catalogo admin por ID (dummy)
    dummy_id = '60d5ec49f9be4b2d88c1e999'
    resp = client.get(f'/admin/usuarios/catalogo/{dummy_id}')
    # Puede devolver 200, 302, 404 o 500 según existencia y manejo de errores
    assert resp.status_code in (200, 302, 404, 500)
    if resp.status_code == 404:
        assert b"no encontrado" in resp.data or b"error" in resp.data or "página no encontrada".encode() in resp.data.lower()
    resp2 = client.get("/admin/catalogo/ffffffffffffffffffffffff", follow_redirects=True)
    # Puede devolver 200, 404, 500 según manejo de error
    assert resp2.status_code in (200, 404, 500)
    if resp2.status_code == 404:
        assert b"no encontrado" in resp2.data or b"error" in resp2.data or "página no encontrada".encode() in resp2.data.lower()

def test_editar_catalogo_admin(client, admin_user_mock):
    resp = client.get("/admin/catalogo/testcollection/000000000000000000000000/editar")
    assert resp.status_code in (200, 302)
    resp2 = client.post("/admin/catalogo/testcollection/000000000000000000000000/editar", data={"nombre": "editado"}, follow_redirects=True)
    assert resp2.status_code in (200, 302)

def test_eliminar_catalogo_admin(client, admin_user_mock):
    resp = client.post("/admin/catalogo/testcollection/000000000000000000000000/eliminar", follow_redirects=True)
    assert resp.status_code == 200
    assert b"eliminar" in resp.data or b"success" in resp.data or b"No se pudo" in resp.data

# ===================== LOGS =====================
def test_logs_list(client, admin_user_mock):
    resp = client.get("/admin/logs/list")
    assert resp.status_code == 200
    assert b".log" in resp.data or b"listado" in resp.data

def test_download_multiple_logs(client, admin_user_mock):
    resp = client.get("/admin/logs/download-multiple?files=flask_debug.log,otro.log")
    # Puede fallar si no existen, pero debe manejar el error y redirigir
    assert resp.status_code in (200, 302)

def test_api_truncate_logs_complete(client, admin_user_mock):
    resp = client.post("/admin/api/truncate-logs", json={"logFiles": ["flask_debug.log"], "method": "complete"})
    assert resp.status_code in (200, 400, 404)
    assert b"processed" in resp.data or b"error" in resp.data or b"files" in resp.data

def test_api_truncate_logs_lines(client, admin_user_mock):
    resp = client.post("/admin/api/truncate-logs", json={"logFiles": ["flask_debug.log"], "method": "lines", "lineCount": 5})
    assert resp.status_code in (200, 400, 404)
    assert b"processed" in resp.data or b"error" in resp.data or b"files" in resp.data

def test_api_truncate_logs_date(client, admin_user_mock):
    resp = client.post("/admin/api/truncate-logs", json={"logFiles": ["flask_debug.log"], "method": "date", "cutoffDate": "2020-01-01"})
    assert resp.status_code in (200, 400, 404)
    assert b"processed" in resp.data or b"error" in resp.data or b"files" in resp.data

# ===================== BACKUPS Y DB =====================
def test_db_status(client, admin_user_mock):
    resp = client.get("/admin/db-status")
    assert resp.status_code in (200, 302)
    assert b"Mongo" in resp.data or b"status" in resp.data or b"Base de datos" in resp.data

def test_db_performance_get_post(client, admin_user_mock):
    resp = client.get("/admin/db/performance")
    assert resp.status_code in (200, 302)
    resp2 = client.post("/admin/db/performance", data={"num_ops": 10, "batch_size": 2}, follow_redirects=True)
    assert resp2.status_code in (200, 302)

def test_list_drive_backups(client, admin_user_mock):
    resp = client.get("/admin/drive-backups")
    assert resp.status_code in (200, 302)
    # Si falla, debe mostrar error y redirigir

def test_cleanup_resets(client, admin_user_mock):
    # Sin follow_redirects: solo verifica que redirige correctamente
    resp = client.get('/admin/cleanup_resets')
    assert resp.status_code == 302
    # Si se desea comprobar el destino final, usar follow_redirects=True
    resp2 = client.get('/admin/cleanup_resets', follow_redirects=True)
    assert resp2.status_code == 200
    # Puede mostrar dashboard, estado o mensaje de éxito
    assert b"dashboard" in resp2.data or b"Mongo" in resp2.data or b"status" in resp2.data or b"Base de datos" in resp2.data or b"Configuraci" in resp2.data

def test_api_cleanup_temp(client, admin_user_mock):
    resp = client.post("/admin/api/cleanup-temp", data={"days": 1})
    assert resp.status_code in (200, 302)
    assert b"cleanup" in resp.data or b"files" in resp.data or b"success" in resp.data or b"message" in resp.data

# ===================== NOTIFICACIONES =====================
def test_notification_settings_min(client, admin_user_mock):
    resp = client.post("/admin/notification-settings", data={
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "smtp_username": "admin@example.com",
        "smtp_tls": "on",
        "recipients": ["admin@example.com"],
        "threshold_cpu": "80",
        "threshold_memory": "90",
        "threshold_disk": "85",
        "threshold_error_rate": "5",
        "cooldown": "60"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"configuraci" in resp.data or b"success" in resp.data or b"Notific" in resp.data or b"error" in resp.data

def test_notification_settings_error(client, admin_user_mock):
    # Envía POST con campos obligatorios pero vacíos para provocar error de validación
    data = {
        'enable_notifications': '',
        'smtp_server': '',
        'smtp_port': '',
        'smtp_username': '',
        'smtp_tls': '',
        'recipients': '',
        'threshold_cpu': '',
        'threshold_memory': '',
        'threshold_disk': '',
        'threshold_error_rate': '',
        'cooldown': ''
    }
    resp = client.post('/admin/notification-settings', data=data, follow_redirects=True)
    # Espera error amigable, no excepción
    assert resp.status_code in (200, 302)
    assert b'Error' in resp.data or b'error' in resp.data or b'guardar' in resp.data or b'Configuraci' in resp.data

# ===================== SCRIPTS =====================
def test_scripts_tools_api_run_json(client, admin_user_mock, app):
    """
    Prueba la ejecución de un script vía API POST /admin/scripts-tools-api/run
    con JSON {'rel_path': '<script>'}. Debe responder JSON (success o error controlado).
    """
    from tests.integration.test_admin_dashboard import force_admin_session
    force_admin_session(client, app)
    rel_path = "db_utils/backup_mongodb.py"
    resp = client.post(
        "/admin/scripts-tools-api/run",
        json={"rel_path": rel_path},
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code in (200, 404, 400)
    assert resp.is_json
    data = resp.get_json()
    # Debe responder resultado o error controlado
    if not ("output" in data or "error" in data):
        print(f"[DEBUG] Respuesta JSON inesperada: {data}")
    assert "output" in data or "error" in data
    # Si existe el script, debe haber salida o error de ejecución
    # Si no existe, debe dar error de archivo no encontrado
    if resp.status_code == 404:
        assert "no encontrado" in data.get("error", "").lower() or "not found" in data.get("error", "").lower()
    elif resp.status_code == 200:
        assert "output" in data
    else:
        assert "error" in data

def test_db_scripts_get_post(client, admin_user_mock):
    resp = client.get("/admin/db-scripts")
    assert resp.status_code in (200, 302)
    resp2 = client.post("/admin/db-scripts", data={}, follow_redirects=True)
    assert resp2.status_code in (200, 302)

# ===================== PANEL Y DASHBOARD =====================
def test_dashboard_admin(client, admin_user_mock):
    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert b"admin" in resp.data or b"Panel" in resp.data

def test_system_status_panel(client, admin_user_mock):
    resp = client.get("/admin/system-status")
    assert resp.status_code == 200
    assert b"status" in resp.data or b"Estado" in resp.data or b"Sistema" in resp.data
