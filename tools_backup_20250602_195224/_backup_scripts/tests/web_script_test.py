#!/usr/bin/env python3
# Script para probar la ejecución de scripts desde la interfaz web
# Este script debe ser ejecutado por el script_runner.py

import os
import sys
import json
import datetime
import subprocess
import traceback

def main():
    """Función principal que realiza pruebas de diagnóstico para la ejecución web"""
    result = {
        "success": True,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tests": []
    }
    
    # Test 1: Verificar el entorno de ejecución
    try:
        result["tests"].append({
            "name": "Entorno de ejecución",
            "success": True,
            "details": {
                "python_version": sys.version,
                "executable": sys.executable,
                "cwd": os.getcwd(),
                "script_path": os.path.abspath(__file__),
                "user": os.getenv('USER', subprocess.getoutput('whoami')),
                "path_env": os.getenv('PATH', 'No disponible')
            }
        })
    except Exception as e:
        result["tests"].append({
            "name": "Entorno de ejecución",
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Test 2: Verificar permisos de archivos
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_scripts = [
            os.path.join(script_dir, "test_script.sh"),
            os.path.join(script_dir, "simple_test.sh")
        ]
        
        file_perms = []
        for script in test_scripts:
            if os.path.exists(script):
                file_perms.append({
                    "path": script,
                    "exists": True,
                    "executable": os.access(script, os.X_OK),
                    "readable": os.access(script, os.R_OK),
                    "size": os.path.getsize(script)
                })
            else:
                file_perms.append({
                    "path": script,
                    "exists": False
                })
        
        result["tests"].append({
            "name": "Permisos de archivos",
            "success": True,
            "details": file_perms
        })
    except Exception as e:
        result["tests"].append({
            "name": "Permisos de archivos",
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Test 3: Probar ejecución de un script simple
    try:
        test_script = os.path.join(script_dir, "simple_test.sh")
        if os.path.exists(test_script):
            process = subprocess.run(
                ['/bin/bash', test_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            result["tests"].append({
                "name": "Ejecución de script",
                "success": process.returncode == 0,
                "details": {
                    "script": test_script,
                    "exit_code": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
            })
        else:
            result["tests"].append({
                "name": "Ejecución de script",
                "success": False,
                "error": f"El script no existe: {test_script}"
            })
    except Exception as e:
        result["tests"].append({
            "name": "Ejecución de script",
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Test 4: Verificar la estructura de directorios
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dirs_to_check = [
            os.path.join(root_dir, "tools"),
            os.path.join(root_dir, "scripts"),
            os.path.join(root_dir, "app"),
            os.path.join(root_dir, "app", "routes")
        ]
        
        dir_structure = []
        for directory in dirs_to_check:
            if os.path.exists(directory):
                dir_structure.append({
                    "path": directory,
                    "exists": True,
                    "is_dir": os.path.isdir(directory),
                    "readable": os.access(directory, os.R_OK),
                    "writable": os.access(directory, os.W_OK),
                    "executable": os.access(directory, os.X_OK)
                })
            else:
                dir_structure.append({
                    "path": directory,
                    "exists": False
                })
        
        result["tests"].append({
            "name": "Estructura de directorios",
            "success": True,
            "details": dir_structure
        })
    except Exception as e:
        result["tests"].append({
            "name": "Estructura de directorios",
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Determinar el éxito general
    result["success"] = all(test.get("success", False) for test in result["tests"])
    
    # Imprimir el resultado como JSON para que lo capture script_runner.py
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
