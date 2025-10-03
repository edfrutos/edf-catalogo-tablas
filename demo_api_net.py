#!/usr/bin/env python3
"""
Script de demostración y pruebas para la API EDF Catálogo de Tablas (.NET)
"""

import requests
import json
import time
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:5003"
API_URL = f"{API_BASE_URL}/api/catalog"

def test_api_connection():
    """Probar la conexión con la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ Conexión exitosa: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_health_check():
    """Probar el endpoint de salud"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Check:")
            print(f"   Estado: {data.get('Status')}")
            print(f"   Puerto: {data.get('Port')}")
            print(f"   Entorno: {data.get('Environment')}")
            print(f"   Timestamp: {data.get('Timestamp')}")
            return True
    except Exception as e:
        print(f"❌ Error en Health Check: {e}")
        return False

def get_all_catalogs():
    """Obtener todos los catálogos"""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Catálogos obtenidos: {len(data.get('catalogs', []))} elementos")
            for i, catalog in enumerate(data.get('catalogs', []), 1):
                print(f"   {i}. {catalog['name']} (ID: {catalog['id']}) - {catalog['numRows']} filas")
            return data.get('catalogs', [])
    except Exception as e:
        print(f"❌ Error obteniendo catálogos: {e}")
        return []

def get_catalog_by_id(catalog_id):
    """Obtener un catálogo específico"""
    try:
        response = requests.get(f"{API_URL}/{catalog_id}")
        if response.status_code == 200:
            data = response.json()
            catalog = data.get('data')
            print(f"✅ Catálogo obtenido:")
            print(f"   Nombre: {catalog['name']}")
            print(f"   Descripción: {catalog['description']}")
            print(f"   Headers: {', '.join(catalog['headers'])}")
            print(f"   Filas: {len(catalog['rows'])}")
            print(f"   Creado por: {catalog['createdBy']}")
            return catalog
        else:
            print(f"❌ Catálogo no encontrado (ID: {catalog_id})")
    except Exception as e:
        print(f"❌ Error obteniendo catálogo: {e}")
        return None

def create_test_catalog():
    """Crear un catálogo de prueba"""
    test_catalog = {
        "name": "Catálogo de Prueba",
        "description": "Este es un catálogo creado para demostrar la funcionalidad",
        "headers": ["ID", "Nombre", "Tipo", "Fecha"]
    }
    
    try:
        response = requests.post(API_URL, json=test_catalog)
        if response.status_code == 201:
            data = response.json()
            catalog = data.get('data')
            print(f"✅ Catálogo creado exitosamente:")
            print(f"   ID: {catalog['id']}")
            print(f"   Nombre: {catalog['name']}")
            return catalog['id']
        else:
            print(f"❌ Error creando catálogo: {response.status_code}")
    except Exception as e:
        print(f"❌ Error creando catálogo: {e}")
        return None

def search_catalogs(search_term):
    """Buscar catálogos"""
    try:
        response = requests.get(f"{API_URL}/search", params={"searchTerm": search_term})
        if response.status_code == 200:
            data = response.json()
            catalogs = data.get('catalogs', [])
            print(f"✅ Búsqueda '{search_term}': {len(catalogs)} resultados")
            for catalog in catalogs:
                print(f"   - {catalog['name']}")
            return catalogs
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return []

def run_demo():
    """Ejecutar la demostración completa"""
    print("🚀 DEMOSTRACIÓN EDF CATÁLOGO DE TABLAS API (.NET 9.0)")
    print("=" * 60)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Probar conexión
    print("1️⃣  PRUEBA DE CONEXIÓN")
    print("-" * 30)
    if not test_api_connection():
        print("❌ No se puede conectar a la API. Asegúrate de que esté ejecutándose.")
        return
    print()
    
    # 2. Health Check
    print("2️⃣  HEALTH CHECK")
    print("-" * 30)
    test_health_check()
    print()
    
    # 3. Obtener catálogos existentes
    print("3️⃣  CATÁLOGOS EXISTENTES")
    print("-" * 30)
    catalogs = get_all_catalogs()
    print()
    
    # 4. Ver detalle de un catálogo
    if catalogs:
        print("4️⃣  DETALLE DE CATÁLOGO")
        print("-" * 30)
        get_catalog_by_id(catalogs[0]['id'])
        print()
    
    # 5. Crear un nuevo catálogo
    print("5️⃣  CREAR NUEVO CATÁLOGO")
    print("-" * 30)
    new_catalog_id = create_test_catalog()
    print()
    
    # 6. Buscar catálogos
    print("6️⃣  BÚSQUEDA DE CATÁLOGOS")
    print("-" * 30)
    search_catalogs("productos")
    search_catalogs("empleados")
    print()
    
    # 7. Listar catálogos actualizados
    print("7️⃣  CATÁLOGOS ACTUALIZADOS")
    print("-" * 30)
    get_all_catalogs()
    print()
    
    print("✅ Demostración completada exitosamente!")
    print(f"🌐 Documentación Swagger: {API_BASE_URL}")

if __name__ == "__main__":
    run_demo()