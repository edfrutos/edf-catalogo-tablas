#!/usr/bin/env python3
"""
Script para probar el endpoint de Google Drive con autenticación
"""
import requests
import json
import os

# Configuración
BASE_URL = "http://localhost:5001"
LOGIN_URL = f"{BASE_URL}/maintenance/login_directo_admin"
GDRIVE_URL = f"{BASE_URL}/maintenance/api/drive-backups"
TEST_GDRIVE_URL = f"{BASE_URL}/maintenance/api/test-gdrive"

# Credenciales de admin
admin_credentials = {
    "username": "edefrutos", 
    "password": "15si34Maf"
}

def test_gdrive_endpoint():
    """Test del endpoint de Google Drive con autenticación"""
    session = requests.Session()
    
    print("🔍 Probando endpoint de Google Drive...")
    print(f"URL de login: {LOGIN_URL}")
    print(f"URL de Google Drive: {GDRIVE_URL}")
    print()
    
    try:
        # 1. Hacer login directo para admin
        print("1️⃣ Realizando login directo admin...")
        login_response = session.get(LOGIN_URL)
        print(f"   Status login: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.text[:200]}")
            return
        
        print("   ✅ Login exitoso")
        
        # 2. Probar endpoint de test de Google Drive (sin autenticación)
        print("\n2️⃣ Probando endpoint de test de Google Drive...")
        test_response = session.get(TEST_GDRIVE_URL)
        print(f"   Status test: {test_response.status_code}")
        
        if test_response.status_code == 200:
            try:
                test_data = test_response.json()
                print("   ✅ Respuesta de test JSON válida:")
                print(json.dumps(test_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"   ⚠️ Test respuesta no es JSON válido: {test_response.text[:500]}")
        else:
            print(f"   ❌ Error en test endpoint:")
            print(f"   Response: {test_response.text[:500]}")
        
        # 3. Llamar al endpoint de Google Drive completo
        print("\n3️⃣ Llamando al endpoint de Google Drive completo...")
        gdrive_response = session.get(GDRIVE_URL)
        print(f"   Status Google Drive: {gdrive_response.status_code}")
        
        if gdrive_response.status_code == 200:
            try:
                data = gdrive_response.json()
                print("   ✅ Respuesta JSON válida:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"   ⚠️ Respuesta no es JSON válido: {gdrive_response.text[:500]}")
        else:
            print(f"   ❌ Error en Google Drive endpoint:")
            print(f"   Response: {gdrive_response.text[:500]}")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("TEST ENDPOINT GOOGLE DRIVE")
    print("=" * 60)
    test_gdrive_endpoint()
    print("\n" + "=" * 60)
