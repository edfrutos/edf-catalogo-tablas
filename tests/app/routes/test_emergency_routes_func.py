import pytest

def test_emergency_admin_login_bypass(client):
    # 1. Acceder a la ruta de bypass sin seguir redirecciones
    resp = client.get("/admin_login_bypass", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin/")

    # 2. Acceder a /admin/ usando la misma sesión
    resp2 = client.get("/admin/")
    # Puede ser 200 (panel admin) o 302 (si requiere más setup)
    assert resp2.status_code in (200, 302)
    # El HTML debe contener "admin", "panel" o "administrador"
    assert b"admin" in resp2.data.lower() or b"panel" in resp2.data.lower() or b"administrador" in resp2.data.lower()
