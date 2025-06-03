#!/usr/bin/env python3
# Script para diagnosticar problemas de ejecución de scripts en la interfaz web
# Este script debe ser ejecutado desde la interfaz web para identificar problemas

import os
import sys
import json
import datetime
import subprocess
import traceback
import platform

def main():
    """Función principal que realiza diagnósticos para la interfaz web"""
    result = {
        "success": True,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "diagnostico": "Diagnóstico de ejecución de scripts en interfaz web",
        "entorno": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "directorio_actual": os.getcwd(),
            "ruta_script": os.path.abspath(__file__),
            "usuario": os.getenv('USER', subprocess.getoutput('whoami')),
            "variables_entorno": {
                "PATH": os.getenv('PATH', 'No disponible'),
                "PYTHONPATH": os.getenv('PYTHONPATH', 'No disponible'),
                "HOME": os.getenv('HOME', 'No disponible')
            }
        },
        "pruebas": []
    }
    
    # Prueba 1: Verificar rutas importantes
    try:
        # Obtener directorio raíz
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        
        # Verificar directorios importantes
        dirs_to_check = {
            "root": root_dir,
            "tools": script_dir,
            "scripts": os.path.join(root_dir, "scripts"),
            "app": os.path.join(root_dir, "app"),
            "routes": os.path.join(root_dir, "app", "routes"),
            "test_scripts": os.path.join(script_dir, "test_scripts")
        }
        
        dir_results = {}
        for name, path in dirs_to_check.items():
            dir_results[name] = {
                "ruta": path,
                "existe": os.path.exists(path),
                "es_directorio": os.path.isdir(path) if os.path.exists(path) else False,
                "permisos_lectura": os.access(path, os.R_OK) if os.path.exists(path) else False,
                "permisos_escritura": os.access(path, os.W_OK) if os.path.exists(path) else False,
                "permisos_ejecucion": os.access(path, os.X_OK) if os.path.exists(path) else False
            }
        
        result["pruebas"].append({
            "nombre": "Verificación de directorios",
            "exito": all(info["existe"] for info in dir_results.values()),
            "resultados": dir_results
        })
    except Exception as e:
        result["pruebas"].append({
            "nombre": "Verificación de directorios",
            "exito": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Prueba 2: Verificar scripts de prueba
    try:
        test_scripts_dir = os.path.join(script_dir, "test_scripts")
        scripts_to_check = [
            os.path.join(test_scripts_dir, "test_script.sh"),
            os.path.join(test_scripts_dir, "simple_test.sh"),
            os.path.join(test_scripts_dir, "simple_test.py"),
            os.path.join(script_dir, "test_script.sh"),
            os.path.join(script_dir, "simple_test.sh")
        ]
        
        script_results = {}
        for script_path in scripts_to_check:
            script_name = os.path.basename(script_path)
            if os.path.exists(script_path):
                script_results[script_name] = {
                    "ruta": script_path,
                    "existe": True,
                    "tamaño": os.path.getsize(script_path),
                    "permisos_lectura": os.access(script_path, os.R_OK),
                    "permisos_ejecucion": os.access(script_path, os.X_OK),
                    "extension": os.path.splitext(script_path)[1]
                }
                
                # Intentar corregir permisos si es necesario
                if not os.access(script_path, os.X_OK):
                    try:
                        os.chmod(script_path, 0o755)
                        script_results[script_name]["permisos_corregidos"] = True
                        script_results[script_name]["permisos_ejecucion"] = os.access(script_path, os.X_OK)
                    except Exception as e:
                        script_results[script_name]["error_permisos"] = str(e)
            else:
                script_results[script_name] = {
                    "ruta": script_path,
                    "existe": False
                }
        
        result["pruebas"].append({
            "nombre": "Verificación de scripts",
            "exito": any(info["existe"] for info in script_results.values()),
            "resultados": script_results
        })
    except Exception as e:
        result["pruebas"].append({
            "nombre": "Verificación de scripts",
            "exito": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Prueba 3: Probar ejecución de un script simple
    try:
        # Buscar un script de prueba que exista
        test_script = None
        for script_path in scripts_to_check:
            if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                test_script = script_path
                break
        
        if test_script:
            # Determinar el comando adecuado según la extensión
            _, ext = os.path.splitext(test_script)
            if ext == '.py':
                cmd = [sys.executable, test_script]
            elif ext == '.sh':
                cmd = ['/bin/bash', test_script]
            else:
                cmd = [test_script]
            
            # Ejecutar el script
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.dirname(test_script)
            )
            
            result["pruebas"].append({
                "nombre": "Ejecución de script",
                "exito": process.returncode == 0,
                "resultados": {
                    "script": test_script,
                    "comando": " ".join(cmd),
                    "codigo_salida": process.returncode,
                    "salida": process.stdout,
                    "error": process.stderr
                }
            })
        else:
            result["pruebas"].append({
                "nombre": "Ejecución de script",
                "exito": False,
                "error": "No se encontró ningún script ejecutable para probar"
            })
    except Exception as e:
        result["pruebas"].append({
            "nombre": "Ejecución de script",
            "exito": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Prueba 4: Verificar la función get_script_path
    try:
        # Implementar una versión simplificada de get_script_path para pruebas
        def get_script_path(script_path):
            # Si ya es una ruta absoluta, usarla directamente
            if os.path.isabs(script_path):
                return script_path
            
            # Construir la ruta absoluta uniendo root_dir y script_path
            abs_script_path = os.path.join(root_dir, script_path)
            
            # Si no existe, intentar añadir 'scripts/' al principio
            if not os.path.exists(abs_script_path):
                if not script_path.startswith('scripts/'):
                    abs_script_path = os.path.join(root_dir, 'scripts', script_path)
            
            # Si sigue sin existir, intentar añadir 'tools/' al principio
            if not os.path.exists(abs_script_path):
                if not script_path.startswith('tools/'):
                    abs_script_path = os.path.join(root_dir, 'tools', script_path)
            
            return abs_script_path
        
        # Probar la función con diferentes rutas
        test_paths = [
            "test_script.sh",
            "tools/test_script.sh",
            "scripts/check_db.py",
            os.path.join(root_dir, "tools", "test_scripts", "simple_test.py"),
            "test_scripts/simple_test.py"
        ]
        
        path_results = {}
        for path in test_paths:
            resolved_path = get_script_path(path)
            path_results[path] = {
                "ruta_original": path,
                "ruta_resuelta": resolved_path,
                "existe": os.path.exists(resolved_path)
            }
        
        result["pruebas"].append({
            "nombre": "Función get_script_path",
            "exito": any(info["existe"] for info in path_results.values()),
            "resultados": path_results
        })
    except Exception as e:
        result["pruebas"].append({
            "nombre": "Función get_script_path",
            "exito": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    
    # Determinar el éxito general
    result["exito"] = all(prueba.get("exito", False) for prueba in result["pruebas"])
    
    # Agregar recomendaciones basadas en los resultados
    result["recomendaciones"] = [
        "Asegúrese de que todos los scripts tengan permisos de ejecución (chmod +x)",
        "Verifique que el usuario del servidor web tenga permisos para acceder a los scripts",
        "Utilice rutas absolutas en lugar de relativas en entornos de producción",
        "Revise los logs de Gunicorn y Flask para obtener más información sobre errores",
        "Asegúrese de que la función get_script_path esté correctamente implementada en scripts_routes.py"
    ]
    
    # Imprimir el resultado como JSON para que lo capture script_runner.py
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
