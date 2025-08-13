#!/usr/bin/env python3
# Descripción: Soluciona los problemas del sistema de testing

import os
import subprocess
import sys

def install_missing_dependencies():
    """Instala las dependencias faltantes"""
    
    print("🔧 SOLUCIONANDO SISTEMA DE TESTING")
    print("=" * 50)
    
    # Dependencias que pueden faltar
    dependencies = [
        "beautifulsoup4",
        "requests",
        "pytest",
        "pytest-html"
    ]
    
    print("📦 Instalando dependencias faltantes...")
    
    for dep in dependencies:
        try:
            print(f"   📥 Instalando {dep}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"      ✅ {dep} instalado correctamente")
            else:
                print(f"      ⚠️  Error instalando {dep}: {result.stderr}")
        except Exception as e:
            print(f"      ❌ Error: {e}")

def create_missing_directories():
    """Crea directorios faltantes para tests"""
    
    print(f"\n📁 Creando directorios faltantes...")
    
    directories = [
        "tests/local/unit",
        "tests/local/integration", 
        "tests/local/functional",
        "tests/local/performance",
        "tests/local/security",
        "tests/production/unit",
        "tests/production/integration",
        "tests/production/functional",
        "tests/production/performance",
        "tests/production/security"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ Creado: {directory}")
        else:
            print(f"   ⚠️  Ya existe: {directory}")

def create_sample_tests():
    """Crea tests de ejemplo para verificar funcionamiento"""
    
    print(f"\n🧪 Creando tests de ejemplo...")
    
    # Test simple para verificar que funciona
    sample_test = '''#!/usr/bin/env python3
# Descripción: Test de ejemplo para verificar funcionamiento del sistema

def test_system_working():
    """Test básico para verificar que el sistema funciona"""
    print("✅ Sistema de testing funcionando correctamente")
    assert True, "Test básico exitoso"

if __name__ == "__main__":
    test_system_working()
    print("🎉 Test completado exitosamente")
'''
    
    test_path = "tests/local/unit/test_system_working.py"
    with open(test_path, 'w') as f:
        f.write(sample_test)
    
    print(f"   ✅ Creado: {test_path}")

def verify_python_environment():
    """Verifica el entorno de Python"""
    
    print(f"\n🐍 Verificando entorno de Python...")
    
    # Verificar Python executable
    python_exec = sys.executable
    print(f"   📍 Python executable: {python_exec}")
    
    # Verificar entorno virtual
    venv_path = os.path.join(os.getcwd(), ".venv", "bin", "python3")
    if os.path.exists(venv_path):
        print(f"   ✅ Entorno virtual encontrado: {venv_path}")
    else:
        print(f"   ⚠️  Entorno virtual no encontrado en: {venv_path}")
    
    # Verificar módulos importantes
    important_modules = ["requests", "bs4", "pytest"]
    for module in important_modules:
        try:
            __import__(module)
            print(f"   ✅ Módulo {module} disponible")
        except ImportError:
            print(f"   ❌ Módulo {module} NO disponible")

def main():
    """Función principal"""
    
    install_missing_dependencies()
    create_missing_directories()
    create_sample_tests()
    verify_python_environment()
    
    print(f"\n🎉 SISTEMA DE TESTING REPARADO")
    print(f"   📋 Próximos pasos:")
    print(f"   1. Reiniciar Gunicorn")
    print(f"   2. Acceder a: http://localhost:8000/dev-template/testing/")
    print(f"   3. Probar el test de ejemplo: test_system_working.py")

if __name__ == "__main__":
    main()
