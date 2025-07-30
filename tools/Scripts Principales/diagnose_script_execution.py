#!/usr/bin/env python3
# Script para diagnosticar problemas de ejecución de scripts desde la interfaz web
# Creado: 18/05/2025

import os
import sys
import json
import subprocess
import datetime
import stat
import re
import platform

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, 'tools')
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
SCRIPT_RUNNER = os.path.join(TOOLS_DIR, 'script_runner.py')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
ROUTES_FILE = os.path.join(ROOT_DIR, 'app/routes/scripts_routes.py')

def print_header(message):
    print("\n" + "="*80)
    print(f"{message}".center(80))
    print("="*80)

def check_script_existence(script_path):
    """Verifica si un script existe y su ubicación"""
    print(f"Verificando script: {script_path}")
    
    # Comprobar si es una ruta absoluta
    if os.path.isabs(script_path):
        if os.path.exists(script_path):
            print(f"  ✅ Script encontrado en ruta absoluta: {script_path}")
            return True, script_path
        else:
            print(f"  ❌ Script no encontrado en ruta absoluta: {script_path}")
    
    # Comprobar en el directorio tools
    tools_path = os.path.join(TOOLS_DIR, script_path)
    if os.path.exists(tools_path):
        print(f"  ✅ Script encontrado en directorio tools: {tools_path}")
        return True, tools_path
    else:
        print(f"  ❌ Script no encontrado en directorio tools: {tools_path}")
    
    # Comprobar en el directorio scripts
    scripts_path = os.path.join(SCRIPTS_DIR, script_path)
    if os.path.exists(scripts_path):
        print(f"  ✅ Script encontrado en directorio scripts: {scripts_path}")
        return True, scripts_path
    else:
        print(f"  ❌ Script no encontrado en directorio scripts: {scripts_path}")
    
    # Comprobar si hay subdirectorios en la ruta
    if '/' in script_path:
        base_dir, script_name = script_path.rsplit('/', 1)
        
        # Comprobar en subdirectorios de tools
        tools_subdir = os.path.join(TOOLS_DIR, base_dir)
        if os.path.exists(tools_subdir):
            for root, dirs, files in os.walk(tools_subdir):
                if script_name in files:
                    full_path = os.path.join(root, script_name)
                    print(f"  ✅ Script encontrado en subdirectorio de tools: {full_path}")
                    return True, full_path
        
        # Comprobar en subdirectorios de scripts
        scripts_subdir = os.path.join(SCRIPTS_DIR, base_dir)
        if os.path.exists(scripts_subdir):
            for root, dirs, files in os.walk(scripts_subdir):
                if script_name in files:
                    full_path = os.path.join(root, script_name)
                    print(f"  ✅ Script encontrado en subdirectorio de scripts: {full_path}")
                    return True, full_path
    
    print(f"  ❌ Script no encontrado en ninguna ubicación")
    return False, None

def check_script_permissions(script_path):
    """Verifica los permisos de un script"""
    if not os.path.exists(script_path):
        print(f"  ❌ No se puede verificar permisos: script no encontrado")
        return False
    
    # Obtener información del archivo
    st = os.stat(script_path)
    permissions = stat.filemode(st.st_mode)
    is_executable = os.access(script_path, os.X_OK)
    is_readable = os.access(script_path, os.R_OK)
    is_writable = os.access(script_path, os.W_OK)
    
    print(f"  Información del script:")
    print(f"    - Permisos: {permissions}")
    print(f"    - Propietario: {st.st_uid}")
    print(f"    - Grupo: {st.st_gid}")
    print(f"    - Tamaño: {st.st_size} bytes")
    print(f"    - Modificado: {datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    - Ejecutable: {'✅ Sí' if is_executable else '❌ No'}")
    print(f"    - Legible: {'✅ Sí' if is_readable else '❌ No'}")
    print(f"    - Escribible: {'✅ Sí' if is_writable else '❌ No'}")
    
    return is_executable

def check_script_content(script_path):
    """Verifica el contenido de un script"""
    if not os.path.exists(script_path):
        print(f"  ❌ No se puede verificar contenido: script no encontrado")
        return False
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Verificar shebang
        first_line = content.split('\n')[0] if content else ""
        has_shebang = first_line.startswith('#!')
        valid_shebang = has_shebang and ('/bin/bash' in first_line or '/usr/bin/env' in first_line)
        
        print(f"  Análisis del contenido:")
        print(f"    - Líneas: {content.count(newline := os.linesep) + 1}")
        print(f"    - Shebang: {'✅ Válido' if valid_shebang else '❌ No válido o ausente'}")
        if has_shebang:
            print(f"    - Shebang encontrado: {first_line}")
        
        # Verificar si requiere root
        requires_root = 'sudo' in content or 'root' in content
        if requires_root:
            print(f"    - ⚠️ El script parece requerir permisos de root")
        
        return True
    except Exception as e:
        print(f"  ❌ Error al leer el contenido: {str(e)}")
        return False

def check_script_runner():
    """Verifica el script_runner.py"""
    if not os.path.exists(SCRIPT_RUNNER):
        print(f"  ❌ script_runner.py no encontrado en: {SCRIPT_RUNNER}")
        return False
    
    # Verificar permisos
    is_executable = os.access(SCRIPT_RUNNER, os.X_OK)
    print(f"  Permisos de script_runner.py:")
    print(f"    - Ejecutable: {'✅ Sí' if is_executable else '❌ No'}")
    
    # Verificar si puede ejecutarse
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_RUNNER],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "Debe especificar la ruta del script a ejecutar" in result.stdout:
            print(f"  ✅ script_runner.py se ejecuta correctamente")
            return True
        else:
            print(f"  ⚠️ script_runner.py se ejecuta pero con salida inesperada")
            print(f"    - Salida: {result.stdout[:100]}...")
            return True
    except Exception as e:
        print(f"  ❌ Error al ejecutar script_runner.py: {str(e)}")
        return False

def check_routes_file():
    """Verifica el archivo de rutas scripts_routes.py"""
    if not os.path.exists(ROUTES_FILE):
        print(f"  ❌ scripts_routes.py no encontrado en: {ROUTES_FILE}")
        return False
    
    try:
        with open(ROUTES_FILE, 'r') as f:
            content = f.read()
        
        # Verificar la función get_script_path
        has_get_script_path = 'def get_script_path' in content
        print(f"  Análisis de scripts_routes.py:")
        print(f"    - Función get_script_path: {'✅ Encontrada' if has_get_script_path else '❌ No encontrada'}")
        
        # Verificar la ruta de ejecución de scripts
        run_script_route = re.search(r'@scripts_bp\.route\([\'"]([^\'"]+)[\'"]\)[^\n]*\ndef run_script', content)
        if run_script_route:
            print(f"    - Ruta para ejecutar scripts: ✅ {run_script_route.group(1)}")
        else:
            print(f"    - Ruta para ejecutar scripts: ❌ No encontrada")
        
        # Verificar blueprint prefix
        blueprint_prefix = re.search(r'scripts_bp = Blueprint\([^\)]+url_prefix=[\'"]([^\'"]+)[\'"]', content)
        if blueprint_prefix:
            print(f"    - Prefijo del blueprint: ✅ {blueprint_prefix.group(1)}")
        else:
            print(f"    - Prefijo del blueprint: ❌ No encontrado")
        
        return True
    except Exception as e:
        print(f"  ❌ Error al leer scripts_routes.py: {str(e)}")
        return False

def test_script_execution(script_path):
    """Prueba la ejecución de un script usando script_runner.py"""
    if not os.path.exists(script_path):
        print(f"  ❌ No se puede probar ejecución: script no encontrado")
        return False
    
    try:
        print(f"  Probando ejecución con script_runner.py...")
        result = subprocess.run(
            [sys.executable, SCRIPT_RUNNER, script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        try:
            result_json = json.loads(result.stdout)
            exit_code = result_json.get('exit_code')
            output = result_json.get('output', '')
            error = result_json.get('error', '')
            
            print(f"    - Código de salida: {exit_code}")
            print(f"    - Salida: {output[:100]}..." if len(output) > 100 else f"    - Salida: {output}")
            print(f"    - Error: {error[:100]}..." if len(error) > 100 else f"    - Error: {error}")
            
            if exit_code == 0:
                print(f"    ✅ Script ejecutado correctamente")
                return True
            else:
                print(f"    ⚠️ Script ejecutado con errores")
                return False
        except json.JSONDecodeError:
            print(f"    ❌ Error al decodificar la salida JSON")
            print(f"    - Salida: {result.stdout[:100]}...")
            print(f"    - Error: {result.stderr[:100]}...")
            return False
    except Exception as e:
        print(f"  ❌ Error al ejecutar el script: {str(e)}")
        return False

def create_test_script():
    """Crea un script de prueba simple"""
    test_script_path = os.path.join(TOOLS_DIR, 'test_script.sh')
    
    try:
        with open(test_script_path, 'w') as f:
            f.write("""#!/bin/bash
# Script de prueba para verificar la ejecución desde la interfaz web
echo "Script de prueba ejecutado correctamente"
echo "Fecha y hora: $(date)"
echo "Usuario: $(whoami)"
echo "Directorio: $(pwd)"
exit 0
""")
        
        os.chmod(test_script_path, 0o755)
        print(f"  ✅ Script de prueba creado en: {test_script_path}")
        return test_script_path
    except Exception as e:
        print(f"  ❌ Error al crear script de prueba: {str(e)}")
        return None

def fix_script_permissions(script_path):
    """Corrige los permisos de un script"""
    if not os.path.exists(script_path):
        print(f"  ❌ No se pueden corregir permisos: script no encontrado")
        return False
    
    try:
        os.chmod(script_path, 0o755)
        print(f"  ✅ Permisos corregidos para: {script_path}")
        return True
    except Exception as e:
        print(f"  ❌ Error al corregir permisos: {str(e)}")
        return False

def main():
    print_header("DIAGNÓSTICO DE EJECUCIÓN DE SCRIPTS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sistema: {platform.platform()}")
    print(f"Python: {sys.version}")
    print(f"Usuario: {os.getenv('USER', subprocess.getoutput('whoami'))}")
    print(f"Directorio raíz: {ROOT_DIR}")
    
    # Verificar script_runner.py
    print_header("VERIFICACIÓN DE SCRIPT_RUNNER.PY")
    check_script_runner()
    
    # Verificar scripts_routes.py
    print_header("VERIFICACIÓN DE SCRIPTS_ROUTES.PY")
    check_routes_file()
    
    # Crear y probar un script de prueba
    print_header("PRUEBA CON SCRIPT DE PRUEBA")
    test_script_path = create_test_script()
    if test_script_path:
        check_script_permissions(test_script_path)
        check_script_content(test_script_path)
        test_script_execution(test_script_path)
    
    # Verificar script específico
    script_name = "supervise_gunicorn.sh"
    print_header(f"VERIFICACIÓN DE SCRIPT ESPECÍFICO: {script_name}")
    
    # Verificar existencia
    exists, script_path = check_script_existence(script_name)
    
    if exists:
        # Verificar permisos
        print_header("VERIFICACIÓN DE PERMISOS")
        if not check_script_permissions(script_path):
            print_header("CORRECCIÓN DE PERMISOS")
            fix_script_permissions(script_path)
        
        # Verificar contenido
        print_header("VERIFICACIÓN DE CONTENIDO")
        check_script_content(script_path)
        
        # Probar ejecución
        print_header("PRUEBA DE EJECUCIÓN")
        test_script_execution(script_path)
    
    # Verificar script alternativo
    alt_script_name = "supervise_gunicorn_web.sh"
    print_header(f"VERIFICACIÓN DE SCRIPT ALTERNATIVO: {alt_script_name}")
    
    # Verificar existencia
    alt_exists, alt_script_path = check_script_existence(alt_script_name)
    
    if alt_exists:
        # Verificar permisos
        print_header("VERIFICACIÓN DE PERMISOS")
        if not check_script_permissions(alt_script_path):
            print_header("CORRECCIÓN DE PERMISOS")
            fix_script_permissions(alt_script_path)
        
        # Verificar contenido
        print_header("VERIFICACIÓN DE CONTENIDO")
        check_script_content(alt_script_path)
        
        # Probar ejecución
        print_header("PRUEBA DE EJECUCIÓN")
        test_script_execution(alt_script_path)
    
    # Recomendaciones
    print_header("RECOMENDACIONES")
    print("1. Asegúrese de que todos los scripts tengan permisos de ejecución (chmod +x)")
    print("2. Evite scripts que requieran permisos de root para ejecutarse desde la interfaz web")
    print("3. Utilice rutas relativas dentro de scripts para mayor portabilidad")
    print("4. Verifique que los scripts tengan el shebang correcto (#!/bin/bash o #!/usr/bin/env python3)")
    print("5. Para scripts que requieren root, cree versiones alternativas que puedan ejecutarse sin privilegios")
    
    print_header("FIN DEL DIAGNÓSTICO")

if __name__ == "__main__":
    main()
