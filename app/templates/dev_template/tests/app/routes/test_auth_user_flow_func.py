import pytest
import string
import random

# Utilidad para generar email aleatorio
def random_email():
    return f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}@example.com"

# Utilidad para generar password aleatorio
def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@pytest.mark.usefixtures("client")
def test_register_login_logout_flow(client):
    email = random_email()
    password = random_password()

    # 1. GET registro
    resp = client.get("/usuarios/register")
    assert resp.status_code == 200
    assert b"registro" in resp.data.lower() or b"registrar" in resp.data.lower()

    # 2. POST registro
    resp = client.post(
        "/usuarios/register",
        data={"email": email, "password": password},
        follow_redirects=True
    )
    # Puede redirigir a login o mostrar mensaje de éxito
    assert resp.status_code in (200, 302)
    assert b"login" in resp.data.lower() or b"iniciar" in resp.data.lower() or b"exito" in resp.data.lower() or b"registrado" in resp.data.lower()

    # 3. POST login (usuario recién registrado)
    resp = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert resp.status_code == 200
    # Debe mostrar panel, dashboard o perfil
    assert b"panel" in resp.data.lower() or b"dashboard" in resp.data.lower() or b"perfil" in resp.data.lower()

    # 4. Acceso a ruta protegida (edit usuario)
    resp = client.get("/usuarios/edit")
    assert resp.status_code == 200
    assert b"usuario" in resp.data.lower() or b"perfil" in resp.data.lower()

    # 5. Logout
    resp = client.get("/usuarios/logout", follow_redirects=True)
    assert resp.status_code == 200
    # Debe mostrar login o portada
    assert b"login" in resp.data.lower() or b"iniciar" in resp.data.lower() or b"panel" in resp.data.lower()

    # 6. Acceso a ruta protegida tras logout (debe redirigir o denegar)
    resp = client.get("/usuarios/edit", follow_redirects=False)
    assert resp.status_code in (302, 401, 403)
