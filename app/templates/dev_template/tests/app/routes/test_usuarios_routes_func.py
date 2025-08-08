import pytest

def test_usuarios_register_route(client):
    resp = client.get("/usuarios/register", follow_redirects=True)
    # Debe responder 200 y mostrar el formulario de registro
    assert resp.status_code == 200
    assert b"registro" in resp.data.lower() or b"registrar" in resp.data.lower()
