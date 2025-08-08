# Script: test_auth_routes_func.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_auth_routes_func.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for

def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower() or b"usuario" in resp.data.lower()

def test_logout_redirect(client):
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code in (200, 302)
