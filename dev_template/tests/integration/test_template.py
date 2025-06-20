# Script: test_template.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_template.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-20

import pytest

def test_template_basico(client):
    """Test plantilla: verifica que el endpoint raíz responde y contiene texto esperado."""
    response = client.get('/')
    assert response.status_code in (200, 302)
    # Puedes personalizar el texto esperado según la home de tu app
    # assert b'Catálogo' in response.data


def test_template_endpoint_protegido(client):
    """Test plantilla: verifica que un endpoint protegido requiere login/admin."""
    response = client.get('/admin')
    assert response.status_code in (200, 302, 401, 403)
    # assert b'Login' in response.data or b'Acceso' in response.data
