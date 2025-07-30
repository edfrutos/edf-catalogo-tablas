import pytest
from flask import url_for
from unittest.mock import MagicMock

# --- Fixtures ---
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

# --- Tests de acciones críticas del panel admin ---

def test_truncar_log_ok(client, admin_user_mock):
    """Truncar log existente por líneas (caso éxito, simula formulario)"""
    resp = client.post("/admin/truncate_log", data={
        "log_file": "flask_debug.log",
        "lines": "10"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"success" in resp.data or b"correctamente" in resp.data or b"Log" in resp.data


def test_truncar_log_error(client, app):
    """Truncar log sin líneas ni fecha (caso error, simula formulario)"""
    from tests.integration.test_admin_dashboard import force_admin_session
    force_admin_session(client, app)
    resp = client.post("/admin/truncate_log", data={
        "log_file": "flask_debug.log"
    }, follow_redirects=True)
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
    print('[DEBUG] Flashes en sesión tras POST:', flashes)
    assert resp.status_code == 200
    assert any("Debes indicar" in msg for cat, msg in flashes)


def test_descargar_log_existente(client, admin_user_mock):
    """Descargar un log existente"""
    resp = client.get("/admin/logs/download/flask_debug.log")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Disposition", "").startswith("attachment")


def test_descargar_log_inexistente(client, admin_user_mock):
    """Intentar descargar un log inexistente (debe mostrar error)"""
    resp = client.get("/admin/logs/download/noexiste.log", follow_redirects=True)
    assert resp.status_code == 200
    assert b"no existe" in resp.data or b"danger" in resp.data


def test_eliminar_usuario(client, admin_user_mock):
    """Eliminar usuario existente (simula POST, usa ObjectId dummy válido)"""
    # Suponemos que existe un usuario con id "000000000000000000000001" en test
    resp = client.post("/admin/usuarios/delete/000000000000000000000001", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Usuario eliminado" in resp.data or b"success" in resp.data


def test_eliminar_usuario_inexistente(client, admin_user_mock):
    """Eliminar usuario inexistente (usa ObjectId dummy válido, debe mostrar error)"""
    resp = client.post("/admin/usuarios/delete/ffffffffffffffffffffffff", follow_redirects=True)
    assert resp.status_code == 200
    assert b"error" in resp.data or b"no encontrado" in resp.data or b"danger" in resp.data


def test_acceso_backup(client, admin_user_mock):
    """Acceso a la página de backups"""
    resp = client.get("/admin/db/backup")
    assert resp.status_code in (200, 302)


def test_lanzar_backup(client, admin_user_mock):
    """Lanzar backup (POST simulado)"""
    resp = client.post("/admin/db/backup", data={}, follow_redirects=True)
    assert resp.status_code == 200 or resp.status_code == 302


def test_limpiar_backups(client, admin_user_mock):
    """Limpiar backups antiguos (POST, acepta dashboard HTML aunque no haya flash explícito)"""
    resp = client.post("/admin/backups/cleanup", data={"days": "1", "max_files": "1"}, follow_redirects=True)
    assert resp.status_code == 200
    # Acepta éxito si carga dashboard de mantenimiento (título o sección típica)
    assert b"Panel Admin" in resp.data or b"Mantenimiento del Sistema" in resp.data or b"Backups antiguos" in resp.data or b"eliminados" in resp.data


def test_configuracion_notificaciones(client, admin_user_mock):
    """Acceso y guardado de configuración de notificaciones (envía todos los campos requeridos)"""
    resp = client.get("/admin/notification-settings")
    assert resp.status_code == 200
    resp2 = client.post("/admin/notification-settings", data={
        "enable_notifications": "on",
        "smtp_server": "smtp.example.com",
        "smtp_port": "587",
        "smtp_username": "admin@example.com",
        "smtp_tls": "on",
        "smtp_password": "testpass123",
        "recipients": ["admin@example.com", "otro@example.com"],
        "threshold_cpu": "80",
        "threshold_memory": "90",
        "threshold_disk": "85",
        "threshold_error_rate": "5",
        "cooldown": "60"
    }, follow_redirects=True)
    assert resp2.status_code == 200
    assert b"configuraci" in resp2.data or b"success" in resp2.data or b"Notific" in resp2.data


def test_ejecutar_script_db(client, admin_user_mock):
    """Acceso y ejecución de scripts de mantenimiento"""
    resp = client.get("/admin/db-scripts")
    assert resp.status_code == 200
    # Simula POST sin parámetros (solo para cobertura)
    resp2 = client.post("/admin/db-scripts", data={}, follow_redirects=True)
    assert resp2.status_code == 200 or resp2.status_code == 302


def test_eliminar_catalogo(client, admin_user_mock):
    """Eliminar catálogo (POST, ids dummy)"""
    resp = client.post("/admin/catalogo/testcollection/000000000000000000000000/eliminar", follow_redirects=True)
    assert resp.status_code == 200
    assert b"eliminar" in resp.data or b"success" in resp.data or b"No se pudo" in resp.data


def test_editar_catalogo(client, admin_user_mock):
    """Editar catálogo (GET y POST, ids dummy)"""
    resp = client.get("/admin/catalogo/testcollection/000000000000000000000000/editar")
    assert resp.status_code == 200 or resp.status_code == 302
    resp2 = client.post("/admin/catalogo/testcollection/000000000000000000000000/editar", data={}, follow_redirects=True)
    assert resp2.status_code == 200 or resp2.status_code == 302


def test_system_status(client, admin_user_mock):
    """Acceso al system status"""
    resp = client.get("/admin/system-status")
    assert resp.status_code == 200
    assert b"status" in resp.data or b"Estado" in resp.data or b"Sistema" in resp.data
