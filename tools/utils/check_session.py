#!/usr/bin/env python3
# Descripción: Verifica la sesión del usuario y su rol

import json

import requests


def check_session():
    """Verifica la sesión del usuario"""

    print("🔍 VERIFICANDO SESIÓN DE USUARIO")
    print("=" * 50)

    # URL base
    base_url = "http://localhost:8000"

    # Crear sesión
    session = requests.Session()

    # Credenciales de administrador
    login_data = {
        'username': 'edefrutos',
        'password': '15si34Maf'
    }

    print("🔐 Iniciando sesión...")
    login_response = session.post(f"{base_url}/auth/login", data=login_data)

    if login_response.status_code != 200:
        print(f"   ❌ Error en login: {login_response.status_code}")
        return False

    print("   ✅ Login exitoso")

    # Verificar cookies de sesión
    print("\n🍪 Verificando cookies de sesión...")
    cookies = session.cookies
    print(f"   📊 Cookies: {dict(cookies)}")

    # Intentar acceder a una página que muestre información de sesión
    print("\n👤 Verificando información de usuario...")

    # Probar diferentes rutas para ver la información de sesión
    test_routes = [
        "/catalogs/",
        "/admin/",
        "/dev-template/testing/"
    ]

    for route in test_routes:
        print(f"   🔗 Probando: {route}")
        response = session.get(f"{base_url}{route}")
        print(f"      📄 Status: {response.status_code}")

        if response.status_code == 200:
            # Buscar información de usuario en el HTML
            html_content = response.text.lower()
            if "admin" in html_content:
                print("      ✅ Contiene 'admin' en la respuesta")
            if "edefrutos" in html_content:
                print("      ✅ Contiene 'edefrutos' en la respuesta")
            if "role" in html_content:
                print("      ✅ Contiene 'role' en la respuesta")
        else:
            print(f"      ❌ Error: {response.status_code}")

    # Intentar acceder directamente a la API con headers
    print("\n🔗 Probando API con headers...")
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }

    api_response = session.get(f"{base_url}/dev-template/testing/api/tests_metadata", headers=headers)
    print(f"   📊 Status: {api_response.status_code}")
    print(f"   📄 Headers: {dict(api_response.headers)}")

    if api_response.status_code == 200:
        try:
            data = api_response.json()
            print("   ✅ JSON válido recibido")
            print(f"   📊 Datos: {json.dumps(data, indent=2)[:200]}...")
        except:
            print("   ❌ No es JSON válido")
            print(f"   📄 Respuesta: {api_response.text[:200]}...")
    else:
        print("   ❌ Error en API")
        print(f"   📄 Respuesta: {api_response.text[:200]}...")

    return True

if __name__ == "__main__":
    check_session()
