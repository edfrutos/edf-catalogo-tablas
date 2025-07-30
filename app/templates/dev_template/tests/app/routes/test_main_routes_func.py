# Script: test_main_routes_func.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_main_routes_func.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for

def test_index_route(client):
    resp = client.get("/")
    # Puede redirigir a welcome si no hay sesión
    assert resp.status_code in (200, 302)

def test_tables_redirect(client):
    resp = client.get("/tables", follow_redirects=True)
    assert resp.status_code == 200
    # Debe contener 'catálogo', 'panel' o 'dashboard' en el HTML
    assert (
        b"cat\xc3\xa1logo" in resp.data.lower() or
        b"panel" in resp.data.lower() or
        b"dashboard" in resp.data.lower()
    )
