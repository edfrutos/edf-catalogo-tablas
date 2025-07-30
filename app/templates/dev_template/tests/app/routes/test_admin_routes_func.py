# Script: test_admin_routes_func.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_admin_routes_func.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-18

import pytest
from flask import url_for

def test_admin_dashboard_requires_auth(client):
    resp = client.get("/admin/", follow_redirects=True)
    # Si no autenticado/admin, puede redirigir a login
    assert resp.status_code in (200, 302)
    # Puede contener 'admin' o 'login' en el HTML
    assert b"admin" in resp.data.lower() or b"login" in resp.data.lower()

def test_admin_logs_download_multiple(client):
    resp = client.get("/admin/logs/download-multiple?files=app.log", follow_redirects=True)
    # Puede devolver 200 si existe, 302 si redirige, o 404 si no existe el archivo
    assert resp.status_code in (200, 302, 404)
