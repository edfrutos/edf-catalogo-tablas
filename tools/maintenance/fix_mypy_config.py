#!/usr/bin/env python3
"""
Script para verificar y corregir la configuración de mypy
"""

import os
import subprocess
import sys


def check_mypy_config():
    """Verifica la configuración de mypy"""
    print("🔍 Verificando configuración de mypy...")

    # Verificar si mypy está instalado
    try:
        result = subprocess.run([sys.executable, '-m', 'mypy', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ mypy instalado: {result.stdout.strip()}")
        else:
            print("❌ mypy no está instalado correctamente")
            return False
    except Exception as e:
        print(f"❌ Error verificando mypy: {e}")
        return False

    # Verificar configuración
    try:
        result = subprocess.run([sys.executable, '-m', 'mypy', '--show-config'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Configuración de mypy válida")
            return True
        else:
            print(f"❌ Error en configuración de mypy: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False

def test_mypy_on_file():
    """Prueba mypy en un archivo simple"""
    print("\n🧪 Probando mypy en un archivo de prueba...")

    # Crear un archivo de prueba simple
    test_file = "test_mypy.py"
    test_content = '''
def test_function(x: int) -> int:
    return x * 2

result = test_function(5)
print(result)
'''

    try:
        with open(test_file, 'w') as f:
            f.write(test_content)

        # Ejecutar mypy en el archivo de prueba
        result = subprocess.run([sys.executable, '-m', 'mypy', test_file],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ mypy funciona correctamente")
            success = True
        else:
            print(f"❌ Error en mypy: {result.stderr}")
            success = False

        # Limpiar archivo de prueba
        os.remove(test_file)
        return success

    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def install_mypy():
    """Instala mypy si no está disponible"""
    print("\n📦 Instalando mypy...")

    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'mypy'],
                              capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("✅ mypy instalado correctamente")
            return True
        else:
            print(f"❌ Error instalando mypy: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error en instalación: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 Verificador de Configuración de mypy")
    print("=" * 50)

    # Verificar configuración
    config_ok = check_mypy_config()

    if not config_ok:
        print("\n🔄 Intentando instalar mypy...")
        if install_mypy():
            config_ok = check_mypy_config()

    if config_ok:
        # Probar mypy
        test_ok = test_mypy_on_file()

        if test_ok:
            print("\n🎉 ¡Configuración de mypy correcta!")
            print("\n📋 Resumen:")
            print("✅ mypy está instalado")
            print("✅ Configuración válida")
            print("✅ Funciona correctamente")
        else:
            print("\n⚠️  mypy está instalado pero hay problemas de configuración")
            print("💡 Revisa los archivos de configuración:")
            print("   - pyproject.toml")
            print("   - mypy.ini")
    else:
        print("\n❌ No se pudo configurar mypy correctamente")
        print("💡 Opciones:")
        print("   1. Instalar mypy manualmente: pip install mypy")
        print("   2. Revisar la configuración en pyproject.toml")
        print("   3. Usar el archivo mypy.ini creado")

if __name__ == "__main__":
    main()
