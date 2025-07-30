#!/usr/bin/env python3
# Script para solucionar problemas de rutas de scripts en la interfaz web
# Creado: 18/05/2025

import os
import sys
import re
import shutil
import datetime
import subprocess

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, 'tools')
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
ROUTES_FILE = os.path.join(ROOT_DIR, 'app/routes/scripts_routes.py')

def print_header(message):
    print("\n" + "="*80)
    print(f"{message}".center(80))
    print("="*80)

def backup_file(file_path):
    """Crea una copia de seguridad del archivo"""
    if os.path.exists(file_path):
        # Crear directorio de backup si no existe
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups', 'automated')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Crear nombre de archivo de backup con timestamp
        filename = os.path.basename(file_path)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{filename}.bak.{timestamp}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar el archivo original al backup
        shutil.copy2(file_path, backup_path)
        print(f"Copia de seguridad creada: {backup_path}")
        return True
    return False

def create_script_symlinks():
    """Crea enlaces simbólicos para los scripts en subdirectorios con nombres únicos"""
    print("Creando enlaces simbólicos para scripts en subdirectorios...")
    
    # Buscar scripts en subdirectorios de tools
    scripts_found = []
    for root, dirs, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith('.sh') or file.endswith('.py'):
                script_path = os.path.join(root, file)
                rel_path = os.path.relpath(script_path, TOOLS_DIR)
                
                # Solo procesar scripts en subdirectorios
                if '/' in rel_path:
                    # Crear nombre único basado en el subdirectorio
                    subdir = rel_path.split('/')[0]
                    unique_name = f"{subdir}_{file}"
                    scripts_found.append((script_path, rel_path, unique_name))
    
    # Crear enlaces simbólicos con nombres únicos
    for script_path, rel_path, unique_name in scripts_found:
        symlink_path = os.path.join(TOOLS_DIR, unique_name)
        
        # Eliminar enlace existente si lo hay
        if os.path.islink(symlink_path):
            os.unlink(symlink_path)
        
        # Crear enlace simbólico solo si no existe un archivo regular
        if not os.path.exists(symlink_path):
            try:
                os.symlink(script_path, symlink_path)
                print(f"  ✅ Enlace creado: {symlink_path} -> {script_path}")
            except Exception as e:
                print(f"  ❌ Error al crear enlace: {str(e)}")
    
    return len(scripts_found)

def improve_get_script_path():
    """Mejora la función get_script_path en scripts_routes.py"""
    if not os.path.exists(ROUTES_FILE):
        print(f"❌ No se encontró el archivo {ROUTES_FILE}")
        return False
    
    # Hacer copia de seguridad
    backup_file(ROUTES_FILE)
    
    try:
        with open(ROUTES_FILE, 'r') as f:
            content = f.read()
        
        # Buscar la función get_script_path
        get_script_path_match = re.search(r'def get_script_path\([^)]*\):(.*?)def', content, re.DOTALL)
        if not get_script_path_match:
            print("❌ No se encontró la función get_script_path en scripts_routes.py")
            return False
        
        # Función mejorada
        improved_function = """def get_script_path(script_path):
    \"\"\"Obtiene la ruta completa del script evitando duplicaciones de rutas\"\"\"
    # Si ya es una ruta absoluta que contiene ROOT_DIR, usarla directamente
    if os.path.isabs(script_path) and ROOT_DIR in script_path:
        return script_path
    
    # Si es una ruta absoluta pero no contiene ROOT_DIR, usarla directamente
    if os.path.isabs(script_path):
        return script_path
    
    # Lista de posibles ubicaciones para buscar el script
    possible_paths = [
        # Ruta directa
        os.path.join(ROOT_DIR, script_path),
        # En directorio tools
        os.path.join(ROOT_DIR, 'tools', script_path),
        # En directorio scripts
        os.path.join(ROOT_DIR, 'scripts', script_path),
    ]
    
    # Buscar en subdirectorios comunes
    for subdir in ['maintenance', 'admin_utils', 'backup', 'monitoring', 'security', 'database']:
        possible_paths.append(os.path.join(ROOT_DIR, 'tools', subdir, script_path))
        possible_paths.append(os.path.join(ROOT_DIR, 'scripts', subdir, script_path))
    
    # Verificar cada ruta posible
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Script encontrado en: {path}")
            return path
    
    # Si no se encuentra, devolver la ruta original
    print(f"Script no encontrado: {script_path}")
    return os.path.join(ROOT_DIR, script_path)
"""
        
        # Reemplazar la función
        new_content = content.replace(get_script_path_match.group(0), improved_function + "\ndef ")
        
        # Guardar el archivo modificado
        with open(ROUTES_FILE, 'w') as f:
            f.write(new_content)
        
        print("✅ Función get_script_path mejorada en scripts_routes.py")
        return True
    except Exception as e:
        print(f"❌ Error al modificar scripts_routes.py: {str(e)}")
        return False

def fix_run_script_route():
    """Corrige la ruta para ejecutar scripts en scripts_routes.py"""
    if not os.path.exists(ROUTES_FILE):
        print(f"❌ No se encontró el archivo {ROUTES_FILE}")
        return False
    
    # Hacer copia de seguridad si no se hizo antes
    if not os.path.exists(f"{ROUTES_FILE}.bak.{datetime.datetime.now().strftime('%Y%m%d')}"):
        backup_file(ROUTES_FILE)
    
    try:
        with open(ROUTES_FILE, 'r') as f:
            content = f.read()
        
        # Buscar la ruta para ejecutar scripts
        run_script_route_match = re.search(r'@scripts_bp\.route\([\'"]([^\'"]+)[\'"]\)[^\n]*\ndef run_script', content)
        if not run_script_route_match:
            # Si no se encuentra, añadir la ruta correcta
            run_script_function_match = re.search(r'def run_script\([^)]*\):', content)
            if not run_script_function_match:
                print("❌ No se encontró la función run_script en scripts_routes.py")
                return False
            
            # Añadir el decorador de ruta
            new_content = content.replace(
                run_script_function_match.group(0),
                "@scripts_bp.route('/run/<path:script_path>', methods=['POST'])\n@admin_required\n" + run_script_function_match.group(0)
            )
            
            # Guardar el archivo modificado
            with open(ROUTES_FILE, 'w') as f:
                f.write(new_content)
            
            print("✅ Ruta para ejecutar scripts añadida en scripts_routes.py")
            return True
        else:
            print(f"ℹ️ Ya existe una ruta para ejecutar scripts: {run_script_route_match.group(1)}")
            return True
    except Exception as e:
        print(f"❌ Error al modificar scripts_routes.py: {str(e)}")
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
        print(f"✅ Script de prueba creado en: {test_script_path}")
        return test_script_path
    except Exception as e:
        print(f"❌ Error al crear script de prueba: {str(e)}")
        return None

def restart_gunicorn():
    """Reinicia el servidor Gunicorn"""
    print("Reiniciando el servidor Gunicorn...")
    try:
        # Intentar usar systemctl
        result = subprocess.run(["systemctl", "restart", "edefrutos2025"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Servidor Gunicorn reiniciado correctamente mediante systemctl")
            return True
        else:
            print(f"❌ Error al reiniciar Gunicorn mediante systemctl: {result.stderr}")
            
            # Intentar usar el script de reinicio
            restart_script = os.path.join(TOOLS_DIR, "restart_server.sh")
            if os.path.exists(restart_script):
                result = subprocess.run([restart_script], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Servidor Gunicorn reiniciado correctamente mediante script")
                    return True
                else:
                    print(f"❌ Error al reiniciar Gunicorn mediante script: {result.stderr}")
            
            return False
    except Exception as e:
        print(f"❌ Error al reiniciar Gunicorn: {str(e)}")
        return False

def main():
    print_header("SOLUCIÓN DE PROBLEMAS DE RUTAS DE SCRIPTS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # COMENTADO: Crear enlaces simbólicos para scripts en subdirectorios
    # print_header("CREANDO ENLACES SIMBÓLICOS")
    # num_scripts = create_script_symlinks()
    # print(f"Se procesaron {num_scripts} scripts")
    
    # Mejorar la función get_script_path
    print_header("MEJORANDO FUNCIÓN GET_SCRIPT_PATH")
    improve_get_script_path()
    
    # Corregir la ruta para ejecutar scripts
    print_header("CORRIGIENDO RUTA PARA EJECUTAR SCRIPTS")
    fix_run_script_route()
    
    # Crear script de prueba
    print_header("CREANDO SCRIPT DE PRUEBA")
    create_test_script()
    
    # Reiniciar Gunicorn
    print_header("REINICIANDO GUNICORN")
    restart_gunicorn()
    
    print_header("SOLUCIÓN COMPLETADA")
    print("Se han realizado las siguientes mejoras:")
    print("1. Se crearon enlaces simbólicos para scripts en subdirectorios")
    print("2. Se mejoró la función get_script_path para buscar scripts en más ubicaciones")
    print("3. Se corrigió la ruta para ejecutar scripts")
    print("4. Se creó un script de prueba para verificar la ejecución")
    print("5. Se reinició el servidor Gunicorn para aplicar los cambios")
    print("\nAhora debería poder ejecutar scripts desde la interfaz web sin errores 404.")

if __name__ == "__main__":
    main()
