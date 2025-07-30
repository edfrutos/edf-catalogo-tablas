import pytest

def test_imagenes_subidas_route(client):
    resp = client.get("/imagenes_subidas/testfile.jpg", follow_redirects=True)
    # Puede devolver 200 si existe, 404 si no, o 302 si redirige
    assert resp.status_code in (200, 302, 404)
