import pytest
from flask import url_for

# Blueprints principales y rutas mínimas a testear
ROUTES = [
    ('main', '/'),
    ('auth', '/login'),
    ('catalogs', '/catalogs/'),
    ('image', '/catalog-images/ping'),  # Suponiendo que existe una ruta de ping/test
    ('usuarios', '/usuarios/'),
    ('admin', '/admin/'),
    ('maintenance', '/admin/maintenance/dashboard'),
    ('errors', '/error/404'),
    ('emergency', '/emergency/'),
    ('debug', '/debug/'),
    ('admin_diagnostic', '/admin/diagnostic/'),
    ('diagnostico', '/diagnostico/')
]

@pytest.mark.parametrize('bp,route', ROUTES)
def test_blueprint_route(client, app, bp, route):
    """
    Testea que la ruta mínima de cada blueprint responde (200, 302, 401, 403, 404) y no lanza error 500.
    """
    resp = client.get(route)
    assert resp.status_code in (200, 302, 401, 403, 404), f"{route} status inesperado: {resp.status_code}"
    assert resp.status_code != 500, f"{route} lanzó error 500"
    # Opcional: loggear la respuesta para debugging
    print(f"Ruta {route} -> status {resp.status_code}")
