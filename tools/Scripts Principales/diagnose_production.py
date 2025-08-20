#!/usr/bin/env python3
# Script para diagnosticar problemas en entorno de producción
# Verifica permisos, rutas y ejecución de scripts

import datetime
import json
import os
import stat
import subprocess
import sys

# Definir el directorio raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def print_header(message):
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80)

def check_file_permissions(file_path):
    """Verifica y muestra los permisos de un archivo"""
    if not os.path.exists(file_path):
        return f"El archivo no existe: {file_path}"

    # Obtener estadísticas del archivo
    st = os.stat(file_path)
    perms = stat.filemode(st.st_mode)
    owner = st.st_uid
    group = st.st_gid

    # Verificar si es ejecutable
    is_executable = os.access(file_path, os.X_OK)

    return {
        "path": file_path,
        "permissions": perms,
        "owner": owner,
        "group": group,
        "is_executable": is_executable,
        "size": st.st_size,
        "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def fix_permissions(file_path):
    """Intenta corregir los permisos de un archivo"""
    if not os.path.exists(file_path):
        return f"El archivo no existe: {file_path}"

    try:
        # Establecer permisos 755 (rwxr-xr-x)
        os.chmod(file_path, 0o755)
        return f"Permisos corregidos para: {file_path}"
    except Exception as e:
        return f"Error al corregir permisos: {str(e)}"

def test_script(script_path):
    """Prueba la ejecución de un script y muestra el resultado"""
    if not os.path.exists(script_path):
        return {
            "success": False,
            "error": f"El script no existe: {script_path}"
        }

    # Verificar y corregir permisos si es necesario
    if not os.access(script_path, os.X_OK):
        fix_permissions(script_path)

    # Determinar el comando según la extensión
    _, ext = os.path.splitext(script_path)
    if ext == '.py':
        cmd = [sys.executable, script_path]
    elif ext == '.sh':
        cmd = ['/bin/bash', script_path]
    else:
        cmd = [script_path]

    try:
        # Ejecutar el script
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.dirname(script_path)
        )

        return {
            "success": process.returncode == 0,
            "output": process.stdout,
            "error": process.stderr,
            "exit_code": process.returncode,
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "El script tardó demasiado tiempo en ejecutarse (más de 10 segundos)",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al ejecutar el script: {str(e)}",
            "command": " ".join(cmd)
        }

def check_web_server_permissions():
    """Verifica los permisos y usuario del servidor web"""
    try:
        # Intentar obtener el usuario actual
        process = subprocess.run(['whoami'], capture_output=True, text=True)
        current_user = process.stdout.strip()

        # Obtener información sobre el proceso del servidor web
        ps_process = subprocess.run(['ps', 'aux', '|', 'grep', 'gunicorn'], shell=True, capture_output=True, text=True)

        return {
            "current_user": current_user,
            "web_server_processes": ps_process.stdout
        }
    except Exception as e:
        return {
            "error": f"Error al verificar permisos del servidor web: {str(e)}"
        }

def main():
    print_header("DIAGNÓSTICO DE SCRIPTS EN PRODUCCIÓN")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio raíz: {ROOT_DIR}")
    print(f"Usuario actual: {os.getenv('USER', subprocess.getoutput('whoami'))}")
    print(f"Directorio actual: {os.getcwd()}")

    # Verificar permisos del servidor web
    print_header("PERMISOS DEL SERVIDOR WEB")
    web_server_info = check_web_server_permissions()
    for key, value in web_server_info.items():
        print(f"{key}: {value}")

    # Verificar scripts de prueba
    test_scripts = [
        os.path.join(ROOT_DIR, "tools", "test_script.sh"),
        os.path.join(ROOT_DIR, "tools", "simple_test.sh"),
        os.path.join(ROOT_DIR, "tools", "test_scripts", "simple_test.py")
    ]

    print_header("VERIFICACIÓN DE PERMISOS DE SCRIPTS")
    for script in test_scripts:
        if os.path.exists(script):
            perms = check_file_permissions(script)
            print(f"Script: {os.path.basename(script)}")
            if isinstance(perms, dict):
                for key, value in perms.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {perms}")
            print()

    print_header("PRUEBA DE EJECUCIÓN DE SCRIPTS")
    for script in test_scripts:
        if os.path.exists(script):
            print(f"Ejecutando: {os.path.basename(script)}")
            result = test_script(script)
            print(f"  Comando: {result.get('command', 'N/A')}")
            print(f"  Éxito: {'Sí' if result.get('success', False) else 'No'}")
            print(f"  Código de salida: {result.get('exit_code', 'N/A')}")
            print(f"  Salida: {result.get('output', '')[:100]}..." if len(result.get('output', '')) > 100 else f"  Salida: {result.get('output', '')}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
            print()

    print_header("RECOMENDACIONES PARA PRODUCCIÓN")
    print("1. Asegúrese de que todos los scripts tengan permisos de ejecución (chmod +x)")
    print("2. Verifique que el usuario del servidor web tenga permisos para ejecutar los scripts")
    print("3. Utilice rutas absolutas en lugar de relativas en entornos de producción")
    print("4. Asegúrese de que los scripts estén en las ubicaciones correctas")
    print("5. Verifique los logs de Gunicorn y Flask para obtener más información sobre errores")

if __name__ == "__main__":
    main()
