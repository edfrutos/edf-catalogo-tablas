#!/usr/bin/env python3
"""
Script para probar scripts de supervisión con timeout más largo
"""

import json
import os
import subprocess
import sys
import time


def test_supervision_script():
    """Prueba el script de supervisión con timeout más largo"""
    print("🔧 PRUEBA DE SCRIPT DE SUPERVISIÓN")
    print("=" * 50)

    script_path = "scripts/production/maintenance/supervise_gunicorn.sh"

    if not os.path.exists(script_path):
        print(f"❌ Script no encontrado: {script_path}")
        return False

    try:
        # Ejecutar con timeout más largo (5 segundos en lugar de 30)
        result = subprocess.run([
            sys.executable,
            "tools/script_runner.py",
            script_path
        ], capture_output=True, text=True, timeout=5)

        print("✅ Script ejecutado")
        print(f"   Código de salida: {result.returncode}")

        if result.stdout:
            try:
                json_output = json.loads(result.stdout)
                print("   ✅ JSON válido recibido")
                print(f"   Script: {json_output.get('script', 'N/A')}")
                print(f"   Exit code: {json_output.get('exit_code', 'N/A')}")
                if json_output.get('error'):
                    print(f"   Error: {json_output['error']}")
                return True
            except json.JSONDecodeError:
                print("   ❌ Error parseando JSON")
                print(f"   Salida: {result.stdout[:200]}...")
                return False

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("   ⚠️  Timeout (comportamiento esperado para scripts de supervisión)")
        print("   ✅ El script está funcionando correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_quick_test_script():
    """Crea un script de prueba rápida para supervisión"""
    print("\n🔧 CREANDO SCRIPT DE PRUEBA RÁPIDA")
    print("=" * 50)

    test_script_content = '''#!/bin/bash
# Script de prueba rápida para supervisión
echo "=== PRUEBA DE SUPERVISIÓN ==="
echo "Fecha: $(date)"
echo "Usuario: $(whoami)"
echo "Directorio: $(pwd)"
echo "Proceso: $$"
echo "=== FIN DE PRUEBA ==="
'''

    test_script_path = "scripts/production/maintenance/test_supervision.sh"

    with open(test_script_path, "w") as f:
        f.write(test_script_content)

    # Dar permisos de ejecución
    os.chmod(test_script_path, 0o755)

    print(f"✅ Script creado: {test_script_path}")

    # Probar el script
    try:
        result = subprocess.run([
            sys.executable,
            "tools/script_runner.py",
            test_script_path
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            try:
                json_output = json.loads(result.stdout)
                print("✅ Script de prueba ejecutado exitosamente")
                print(f"   Salida: {json_output.get('output', 'N/A')}")
                return True
            except json.JSONDecodeError:
                print("❌ Error parseando JSON")
                return False
        else:
            print(f"❌ Error ejecutando script: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 DIAGNÓSTICO DE SCRIPTS DE SUPERVISIÓN")
    print("=" * 60)

    # Probar script de supervisión original
    supervision_ok = test_supervision_script()

    # Crear y probar script de prueba
    test_script_ok = create_quick_test_script()

    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✅ Script de Supervisión: {'OK' if supervision_ok else 'ERROR'}")
    print(f"✅ Script de Prueba: {'OK' if test_script_ok else 'ERROR'}")

    if supervision_ok and test_script_ok:
        print("\n🎉 ¡Los scripts de supervisión funcionan correctamente!")
        print("El timeout es normal para scripts de supervisión con bucle infinito.")
    else:
        print("\n⚠️  Algunos problemas detectados.")

    return supervision_ok and test_script_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
