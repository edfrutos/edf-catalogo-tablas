# Script: test_auth.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_auth.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import pytest

@pytest.fixture
def client(app):
    return app.test_client()

def test_register_user(client):
    response = client.post('/register', data={
        'nombre': 'TestUser',
        'email': 'testuser@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'Registro exitoso' in data or '¡Registro exitoso!' in data

def test_login_success(client):
    # Registrar usuario primero
    client.post('/register', data={
        'nombre': 'TestLogin',
        'email': 'testlogin@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Login correcto
    response = client.post('/login', data={
        'login_input': 'testlogin@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'Inicio de sesi' in data or 'dashboard' in data

def test_login_fail(client):
    response = client.post('/login', data={
        'login_input': 'noexiste@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'Usuario no encontrado' in data or 'Credenciales inv' in data

def test_logout(client):
    # Registrar y loguear
    client.post('/register', data={
        'nombre': 'TestLogout',
        'email': 'testlogout@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'testlogout@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Logout
    response = client.get('/logout', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'login' in data or 'cerrado sesi' in data

def test_forgot_password(client):
    client.post('/register', data={
        'nombre': 'TestForgot',
        'email': 'testforgot@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.post('/forgot-password', data={
        'usuario': 'testforgot@example.com'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'recuperación' in data or 'enlace' in data or 'correo' in data

def test_protected_route_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'iniciar sesión' in data or 'login' in data or 'Debes iniciar sesión' in data

def test_user_dashboard_access(client):
    client.post('/register', data={
        'nombre': 'TestPanel',
        'email': 'testpanel@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'testpanel@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/dashboard_user', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'tablas' in data or 'catálogo' in data or 'usuario' in data

def test_tables_access_after_login(client):
    client.post('/register', data={
        'nombre': 'TestTables',
        'email': 'testtables@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'testtables@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/tables', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'tablas' in data or 'catálogo' in data or 'crear' in data

def test_admin_panel_access(client, app):
    # Crear usuario admin directamente en la base de datos
    with app.app_context():
        admin_email = 'admintest@example.com'
        admin_user = app.users_collection.find_one({'email': admin_email})
        if not admin_user:
            from werkzeug.security import generate_password_hash
            app.users_collection.insert_one({
                'nombre': 'AdminTest',
                'email': admin_email,
                'password': generate_password_hash('adminpass'),
                'role': 'admin',
                'username': 'admintest'
            })
    # Login como admin
    client.post('/login', data={
        'login_input': 'admintest@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    response = client.get('/admin/', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'admin' in data or 'panel' in data or 'usuarios' in data

def test_user_cannot_access_admin_panel(client):
    client.post('/register', data={
        'nombre': 'TestNoAdmin',
        'email': 'testnoadmin@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'testnoadmin@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/admin/', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'acceso' in data or 'login' in data

def test_admin_cannot_access_user_dashboard(client, app):
    # Login como admin
    client.post('/login', data={
        'login_input': 'admintest@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    response = client.get('/dashboard_user', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'acceso' in data or 'admin' in data

def test_user_cannot_edit_other_user_table(client, app):
    # Registrar dos usuarios
    client.post('/register', data={
        'nombre': 'UserA',
        'email': 'usera@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/register', data={
        'nombre': 'UserB',
        'email': 'userb@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Login como UserA y crear tabla
    client.post('/login', data={
        'login_input': 'usera@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    with app.app_context():
        table_id = app.spreadsheets_collection.insert_one({
            'owner': 'UserA',
            'name': 'TablaUserA',
            'headers': ['Col1'],
            'data': []
        }).inserted_id
    client.get('/logout', follow_redirects=True)
    # Login como UserB e intenta editar tabla de UserA
    client.post('/login', data={
        'login_input': 'userb@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get(f'/editar/{table_id}', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'No tiene permisos' in data
    # Limpieza
    with app.app_context():
        app.spreadsheets_collection.delete_one({'_id': table_id})

def test_user_cannot_delete_other_user_table(client, app):
    # Registrar dos usuarios
    client.post('/register', data={
        'nombre': 'UserC',
        'email': 'userc@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/register', data={
        'nombre': 'UserD',
        'email': 'userd@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Login como UserC y crear tabla
    client.post('/login', data={
        'login_input': 'userc@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    with app.app_context():
        table_id = app.spreadsheets_collection.insert_one({
            'owner': 'UserC',
            'name': 'TablaUserC',
            'headers': ['Col1'],
            'data': []
        }).inserted_id
    client.get('/logout', follow_redirects=True)
    # Login como UserD e intenta eliminar tabla de UserC
    client.post('/login', data={
        'login_input': 'userd@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.post(f'/delete_table/{table_id}', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'No tiene permisos' in data
    # Limpieza
    with app.app_context():
        app.spreadsheets_collection.delete_one({'_id': table_id})

def test_admin_can_edit_and_delete_any_table(client, app):
    # Crear usuario admin
    with app.app_context():
        admin_email = 'adminpermisos@example.com'
        admin_user = app.users_collection.find_one({'email': admin_email})
        if not admin_user:
            from werkzeug.security import generate_password_hash
            app.users_collection.insert_one({
                'nombre': 'AdminPermisos',
                'email': admin_email,
                'password': generate_password_hash('adminpass'),
                'role': 'admin',
                'username': 'adminpermisos'
            })
    # Crear tabla de otro usuario
    with app.app_context():
        table_id = app.spreadsheets_collection.insert_one({
            'owner': 'OtroUsuario',
            'name': 'TablaAjena',
            'headers': ['Col1'],
            'data': []
        }).inserted_id
    # Login como admin
    client.post('/login', data={
        'login_input': 'adminpermisos@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    # Puede editar
    response = client.get(f'/editar/{table_id}', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'Tabla' in data or 'Editar' in data
    # Puede eliminar
    response = client.post(f'/delete_table/{table_id}', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'eliminada' in data or 'exitosamente' in data
    # Limpieza
    with app.app_context():
        app.spreadsheets_collection.delete_one({'_id': table_id})

def test_forced_password_change_flow(client, app):
    # Crear usuario con must_change_password
    with app.app_context():
        email = 'forcechange@example.com'
        from werkzeug.security import generate_password_hash
        app.users_collection.insert_one({
            'nombre': 'ForceChange',
            'email': email,
            'password': 'RESET_REQUIRED',
            'role': 'user',
            'must_change_password': True,
            'username': 'forcechange'
        })
    # Login debe redirigir a cambio de contraseña
    response = client.post('/login', data={
        'login_input': email,
        'password': 'cualquier',
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'nueva contraseña' in data or 'crear una nueva contraseña' in data
    # Limpieza
    with app.app_context():
        app.users_collection.delete_one({'email': email})

def test_account_lock_after_failed_attempts(client, app):
    # Crear usuario
    email = 'locktest@example.com'
    client.post('/register', data={
        'nombre': 'LockTest',
        'email': email,
        'password': 'lockpass'
    }, follow_redirects=True)
    # 5 intentos fallidos
    for _ in range(5):
        client.post('/login', data={
            'login_input': email,
            'password': 'wrongpass'
        }, follow_redirects=True)
    # Ahora debe estar bloqueada
    response = client.post('/login', data={
        'login_input': email,
        'password': 'lockpass'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'bloqueada' in data or '15 minutos' in data
    # Limpieza
    with app.app_context():
        app.users_collection.delete_one({'email': email})

def test_admin_settings_access(client, app):
    # Login como admin
    client.post('/login', data={
        'login_input': 'admintest@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    response = client.get('/admin/notification-settings', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'notific' in data or 'configuración' in data

def test_non_admin_cannot_access_admin_settings(client):
    # Registrar y loguear usuario normal
    client.post('/register', data={
        'nombre': 'NoAdminSettings',
        'email': 'noadminsettings@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'noadminsettings@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/admin/notification-settings', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'acceso' in data or 'admin' in data

def test_logs_access_only_admin(client, app):
    # Login como admin
    client.post('/login', data={
        'login_input': 'admintest@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    response = client.get('/admin/logs', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'logs' in data or 'registro' in data
    # Logout y login como usuario normal
    client.get('/logout', follow_redirects=True)
    client.post('/register', data={
        'nombre': 'NoAdminLogs',
        'email': 'noadminlogs@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'noadminlogs@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/admin/logs', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'acceso' in data or 'admin' in data

def test_user_can_edit_own_profile(client, app):
    # Registrar y loguear
    client.post('/register', data={
        'nombre': 'EditProfile',
        'email': 'editprofile@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'editprofile@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.post('/profile/edit', data={
        'nombre': 'Editado',
        'email': 'editprofile@example.com'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'perfil' in data or 'actualizado' in data or 'éxito' in data

def test_user_cannot_edit_other_profile(client, app):
    # Registrar dos usuarios
    client.post('/register', data={
        'nombre': 'UserE',
        'email': 'usere@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/register', data={
        'nombre': 'UserF',
        'email': 'userf@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Login como UserE
    client.post('/login', data={
        'login_input': 'usere@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    # Intenta editar perfil de UserF
    response = client.post('/profile/edit', data={
        'nombre': 'Hack',
        'email': 'userf@example.com'
    }, follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'permiso' in data or 'acceso' in data or 'No puedes' in data

def test_access_after_logout(client):
    # Registrar y loguear
    client.post('/register', data={
        'nombre': 'LogoutTest',
        'email': 'logouttest@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.post('/login', data={
        'login_input': 'logouttest@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    client.get('/logout', follow_redirects=True)
    response = client.get('/dashboard', follow_redirects=True)
    data = response.data.decode('utf-8')
    assert 'iniciar sesión' in data or 'login' in data or 'Debes iniciar sesión' in data

def test_direct_access_only_in_dev(client, app):
    # Acceso directo admin solo permitido en desarrollo
    with app.app_context():
        env = app.config.get('ENV', 'production')
    response = client.get('/direct_admin', follow_redirects=True)
    data = response.data.decode('utf-8')
    if env == 'development':
        assert 'admin' in data or 'panel' in data
    else:
        assert 'no autorizado' in data or 'prohibido' in data or 'login' in data 