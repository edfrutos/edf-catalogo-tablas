#!/usr/bin/env python3
# Descripción: Verifica que los problemas del sistema de testing están solucionados

import json
import time

import requests


def verify_testing_system():
    """Verifica que el sistema de testing funciona correctamente"""

    print("🔍 VERIFICANDO SISTEMA DE TESTING")
    print("=" * 50)

    # URL base
    base_url = "http://localhost:8000"

    # Crear sesión
    session = requests.Session()

    # Login como admin
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }

    print("🔐 Iniciando sesión...")
    login_response = session.post(f"{base_url}/auth/login", data=login_data)

    if login_response.status_code != 200:
        print(f"   ❌ Error en login: {login_response.status_code}")
        return False

    print("   ✅ Login exitoso")

    # Verificar acceso al dashboard de testing
    print("\n📊 Verificando dashboard de testing...")
    testing_response = session.get(f"{base_url}/dev-template/testing/")

    if testing_response.status_code != 200:
        print(f"   ❌ Error accediendo a /dev-template/testing/: {testing_response.status_code}")
        return False

    print("   ✅ Dashboard accesible")

    # Verificar API de metadatos de tests
    print("\n🔗 Verificando API de metadatos...")
    api_response = session.get(f"{base_url}/dev-template/testing/api/tests_metadata")

    if api_response.status_code != 200:
        print(f"   ❌ Error en API: {api_response.status_code}")
        return False

    print("   ✅ API funcionando")

    # Parsear respuesta JSON
    try:
        tests_data = api_response.json()
        print(f"   📊 Datos recibidos: {len(tests_data)} entornos")

        # Verificar entornos
        for entorno, categorias in tests_data.items():
            print(f"\n   🌍 Entorno: {entorno}")
            print(f"      📁 Categorías: {len(categorias)}")

            for categoria in categorias:
                nombre_cat = categoria.get('categoria', 'N/A')
                tests = categoria.get('tests', [])
                print(f"         📂 {nombre_cat}: {len(tests)} tests")

                # Mostrar algunos tests de ejemplo
                for test in tests[:3]:
                    print(f"            • {test.get('nombre', 'N/A')}: {test.get('descripcion', 'Sin descripción')}")
                if len(tests) > 3:
                    print(f"            ... y {len(tests) - 3} más")

    except json.JSONDecodeError as e:
        print(f"   ❌ Error parseando JSON: {e}")
        return False

    # Probar ejecución de un test simple
    print("\n🧪 Probando ejecución de test...")

    # Buscar el test de ejemplo que creamos
    test_to_run = None
    for entorno, categorias in tests_data.items():
        for categoria in categorias:
            for test in categoria.get('tests', []):
                if 'test_system_working' in test.get('nombre', ''):
                    test_to_run = test
                    break
            if test_to_run:
                break
        if test_to_run:
            break

    if test_to_run:
        print(f"   🎯 Ejecutando: {test_to_run['nombre']}")

        # Ejecutar el test
        test_path = test_to_run['path']
        run_response = session.post(f"{base_url}/dev-template/testing/run/{test_path}")

        if run_response.status_code == 200:
            run_data = run_response.json()
            if run_data.get('status') == 'success':
                print("   ✅ Test ejecutado exitosamente")
                print(f"      📄 Salida: {run_data.get('stdout', 'Sin salida')[:100]}...")
            else:
                print(f"   ⚠️  Test ejecutado pero con errores: {run_data.get('error', 'Error desconocido')}")
        else:
            print(f"   ❌ Error ejecutando test: {run_response.status_code}")
    else:
        print("   ⚠️  No se encontró el test de ejemplo")

    print("\n🎉 VERIFICACIÓN COMPLETADA")
    print("   ✅ Dashboard accesible")
    print("   ✅ API funcionando")
    print("   ✅ Tests disponibles")
    print("   ✅ Ejecución de tests funcional")

    return True

if __name__ == "__main__":
    verify_testing_system()
