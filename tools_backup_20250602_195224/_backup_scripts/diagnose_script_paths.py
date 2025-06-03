#!/usr/bin/env python3
# Script para diagnosticar problemas con las rutas de scripts
# Este script ayuda a identificar problemas con las rutas y permisos de los scripts

import os
import sys
import glob
import subprocess
import json

# Definir el directorio raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def print_header(message):
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80)

def get_script_path(script_path):
    """Implementación de la función get_script_path para pruebas"""
    # Si ya es una ruta absoluta que contiene ROOT_DIR, usarla directamente
    if ROOT_DIR in script_path:
        return script_path
    
    # Si es una ruta absoluta pero no contiene ROOT_DIR, usarla directamente
    if os.path.isabs(script_path):
        return script_path
    
    # Construir la ruta absoluta uniendo ROOT_DIR y script_path
    abs_script_path = os.path.join(ROOT_DIR, script_path)
    
    # Si no existe, intentar añadir 'scripts/' al principio si no lo tiene ya
    if not os.path.exists(abs_script_path):
        if not script_path.startswith('scripts/'):
            abs_script_path = os.path.join(ROOT_DIR, 'scripts', script_path)
    
    # Si sigue sin existir, intentar añadir 'tools/' al principio si no lo tiene ya
    if not os.path.exists(abs_script_path):
        if not script_path.startswith('tools/'):
            abs_script_path = os.path.join(ROOT_DIR, 'tools', script_path)
    
    return abs_script_path

def test_script_execution(script_path):
    """Prueba la ejecución de un script y devuelve el resultado"""
    abs_script_path = get_script_path(script_path)
    
    print(f"Probando script: {script_path}")
    print(f"Ruta absoluta: {abs_script_path}")
    print(f"Existe: {'Sí' if os.path.exists(abs_script_path) else 'No'}")
    
    if not os.path.exists(abs_script_path):
        return {
            "success": False,
            "error": f"El script no existe: {abs_script_path}",
            "output": "",
            "exit_code": -1
        }
    
    print(f"Permisos de ejecución: {'Sí' if os.access(abs_script_path, os.X_OK) else 'No'}")
    
    # Si no tiene permisos de ejecución, intentar establecerlos
    if not os.access(abs_script_path, os.X_OK):
        try:
            os.chmod(abs_script_path, 0o755)
            print("Permisos de ejecución establecidos")
        except Exception as e:
            print(f"Error al establecer permisos: {str(e)}")
            return {
                "success": False,
                "error": f"No se pudieron establecer permisos de ejecución: {str(e)}",
                "output": "",
                "exit_code": -1
            }
    
    # Ejecutar el script
    try:
        # Determinar el comando adecuado según la extensión
        _, ext = os.path.splitext(abs_script_path)
        if ext == '.py':
            cmd = [sys.executable, abs_script_path]
        elif ext == '.sh':
            cmd = ['/bin/bash', abs_script_path]
        else:
            cmd = [abs_script_path]
        
        # Ejecutar el script
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.dirname(abs_script_path)
        )
        
        return {
            "success": process.returncode == 0,
            "output": process.stdout,
            "error": process.stderr,
            "exit_code": process.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "El script tardó demasiado tiempo en ejecutarse (más de 10 segundos)",
            "output": "",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al ejecutar el script: {str(e)}",
            "output": "",
            "exit_code": -1
        }

def main():
    print_header("DIAGNÓSTICO DE RUTAS DE SCRIPTS")
    print(f"Directorio raíz: {ROOT_DIR}")
    
    # Probar la función get_script_path con diferentes rutas
    print_header("PRUEBA DE RESOLUCIÓN DE RUTAS")
    test_paths = [
        "simple_test.sh",
        "tools/simple_test.sh",
        "scripts/check_db.py",
        "/tools/test_scripts/simple_test.py",
        "test_scripts/simple_test.py"
    ]
    
    for path in test_paths:
        resolved_path = get_script_path(path)
        print(f"Ruta original: {path}")
        print(f"Ruta resuelta: {resolved_path}")
        print(f"Existe: {'Sí' if os.path.exists(resolved_path) else 'No'}")
        print()
    
    # Probar la ejecución de scripts
    print_header("PRUEBA DE EJECUCIÓN DE SCRIPTS")
    test_scripts = [
        "tools/test_scripts/simple_test.py",
        "tools/simple_test.sh"
    ]
    
    for script in test_scripts:
        result = test_script_execution(script)
        print(f"Resultado: {'Éxito' if result['success'] else 'Error'}")
        print(f"Código de salida: {result['exit_code']}")
        print(f"Salida: {result['output']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print()
    
    print_header("RECOMENDACIONES")
    print("1. Asegúrese de que todos los scripts tengan permisos de ejecución (chmod +x)")
    print("2. Verifique que los scripts existan en las ubicaciones esperadas")
    print("3. Para scripts Python, asegúrese de que tengan la línea shebang: #!/usr/bin/env python3")
    print("4. Para scripts Bash, asegúrese de que tengan la línea shebang: #!/bin/bash")
    print("5. Utilice la función get_script_path para resolver rutas de scripts")

if __name__ == "__main__":
    main()
