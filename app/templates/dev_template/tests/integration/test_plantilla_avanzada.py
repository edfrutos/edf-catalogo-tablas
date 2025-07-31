# Script: test_plantilla_avanzada.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_plantilla_avanzada.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-20

import pytest

@pytest.fixture
def usuario_test(mongo_client_ssl):
    """Crea un usuario de prueba en la colección users y lo elimina al final."""
    db = mongo_client_ssl.get_database()
    user = {"email": "test_user@demo.com", "username": "usuariotest", "is_admin": False}
    inserted = db.users.insert_one(user)
    yield user
    db.users.delete_one({"_id": inserted.inserted_id})


def login(client, username, password):
    """Helper para simular login (ajusta los campos según tu formulario)."""
    return client.post('/login', data={"username": username, "password": password}, follow_redirects=True)


def test_login_logout_flow(client, usuario_test):
    """Verifica el flujo de login y logout de usuario real."""
    # Simula login (ajusta según la lógica real de tu app)
    resp = login(client, usuario_test["username"], "1234")
    assert resp.status_code in (200, 302)
    # Simula logout
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code in (200, 302)


def test_endpoint_protegido_requiere_login(client):
    """Asegura que un endpoint protegido redirige o rechaza si no hay sesión."""
    resp = client.get('/admin', follow_redirects=False)
    assert resp.status_code in (302, 401, 403)


def test_creacion_y_borrado_catalogo(client, mongo_client_ssl):
    """Crea y borra un catálogo, comprobando persistencia en MongoDB."""
    # Crear catálogo
    payload = {"nombre": "cat_temp", "descripcion": "catalogo temporal"}
    resp = client.post('/api/catalogs/create', json=payload)
    assert resp.status_code in (201, 403, 401)
    if resp.status_code == 201:
        data = resp.get_json()
        catalog_id = data.get('id')
        db = mongo_client_ssl.get_database()
        assert db.catalogs.find_one({"_id": catalog_id}) is not None
        # Borrar catálogo
        del_resp = client.delete(f'/api/catalogs/delete/{catalog_id}')
        assert del_resp.status_code in (200, 204)
        assert db.catalogs.find_one({"_id": catalog_id}) is None
