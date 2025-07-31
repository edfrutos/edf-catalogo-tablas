#!/usr/bin/env python3
# Script para organizar los scripts que están en el directorio raíz de /tools
# Creado: 18/05/2025

import os
import sys
import shutil
import datetime

# Configuración
ROOT_DIR = '/var/www/vhosts/edefrutos2025.xyz/httpdocs'
TOOLS_DIR = os.path.join(ROOT_DIR, 'tools')

def print_header(message):
    print("\n" + "="*80)
    print(f"{message}".center(80))
    print("="*80)

def ensure_directory(directory):
    """Asegura que un directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"✅ Directorio creado: {directory}")
    return directory

def organize_scripts():
    """Organiza los scripts que están directamente en /tools"""
    print("Organizando scripts en el directorio raíz de /tools...")
    
    # Definir categorías y patrones de nombres de archivos
    categories = {
        'admin_utils': ['admin', 'user', 'permission', 'role', 'unlock'],
        'db_utils': ['db', 'mongo', 'database', 'collection', 'catalog'],
        'maintenance': ['maintenance', 'backup', 'clean', 'update', 'monitor', 'supervise', 'start', 'stop', 'restart', 'iniciar', 'run', 'gunicorn'],
        'monitoring': ['monitor', 'check', 'diagnose', 'log', 'status', 'health', 'report'],
        'aws_utils': ['aws', 's3', 'bucket', 'cloud'],
        'image_utils': ['image', 'photo', 'picture', 'thumbnail'],
        'session_utils': ['session', 'cookie', 'auth', 'login'],
        'system': ['system', 'os', 'process', 'service', 'daemon', 'socket'],
        'utils': ['util', 'helper', 'tool', 'test', 'simple', 'prueba']
    }
    
    # Scripts que deben permanecer en el directorio raíz
    keep_in_root = [
        'script_runner.py',
        'fix_script_paths.py',
        'migrate_scripts.py',
        'cleanup_tools_directory.py',
        'organize_root_scripts.py',
        'test_script_execution.py',
        '__init__.py'
    ]
    
    # Asegurar que los subdirectorios existen
    for category in categories:
        ensure_directory(os.path.join(TOOLS_DIR, category))
    
    # Listar todos los scripts en el directorio raíz de /tools
    scripts_moved = 0
    for item in os.listdir(TOOLS_DIR):
        source_item = os.path.join(TOOLS_DIR, item)
        
        # Solo procesar archivos, no directorios ni enlaces simbólicos
        if os.path.isfile(source_item) and not os.path.islink(source_item) and (item.endswith('.py') or item.endswith('.sh')):
            # Ignorar archivos específicos que deben permanecer en el directorio raíz
            if item in keep_in_root:
                print(f"  ℹ️ Manteniendo en raíz: {item}")
                continue
            
            # Determinar la categoría del script
            category = None
            for cat, patterns in categories.items():
                for pattern in patterns:
                    if pattern.lower() in item.lower():
                        category = cat
                        break
                if category:
                    break
            
            # Si no se encontró una categoría, usar 'utils'
            if not category:
                category = 'utils'
            
            # Mover el script a su categoría
            target_dir = os.path.join(TOOLS_DIR, category)
            target_item = os.path.join(target_dir, item)
            
            # Verificar si el archivo ya existe en el destino
            if os.path.exists(target_item):
                print(f"  ⚠️ El archivo ya existe en el destino: {target_item}")
                continue
            
            # Mover el archivo
            shutil.move(source_item, target_item)
            print(f"  ✅ Archivo categorizado: {item} -> {category}")
            scripts_moved += 1
    
    print(f"Se categorizaron {scripts_moved} scripts del directorio raíz")
    return scripts_moved

def run_fix_script_paths():
    """Ejecuta el script fix_script_paths.py"""
    print("Ejecutando fix_script_paths.py...")
    
    fix_script = os.path.join(TOOLS_DIR, 'fix_script_paths.py')
    if not os.path.exists(fix_script):
        print(f"❌ No se encontró el script {fix_script}")
        return False
    
    try:
        # Hacer el script ejecutable
        os.chmod(fix_script, 0o755)
        
        # Ejecutar el script
        result = os.system(fix_script)
        
        if result == 0:
            print("✅ fix_script_paths.py ejecutado correctamente")
            return True
        else:
            print(f"❌ Error al ejecutar fix_script_paths.py (código {result})")
            return False
    except Exception as e:
        print(f"❌ Error al ejecutar fix_script_paths.py: {str(e)}")
        return False

def restart_service():
    """Reinicia el servicio edefrutos2025"""
    print("Reiniciando el servicio edefrutos2025...")
    
    try:
        result = os.system('systemctl restart edefrutos2025')
        
        if result == 0:
            print("✅ Servicio reiniciado correctamente")
            
            # Verificar el estado del servicio
            status_result = os.system('systemctl status edefrutos2025 | grep "Active: active (running)"')
            if status_result == 0:
                print("✅ El servicio está activo y en ejecución")
                return True
            else:
                print("❌ El servicio no está en ejecución")
                return False
        else:
            print(f"❌ Error al reiniciar el servicio (código {result})")
            return False
    except Exception as e:
        print(f"❌ Error al reiniciar el servicio: {str(e)}")
        return False

def main():
    print_header("ORGANIZACIÓN DE SCRIPTS EN EL DIRECTORIO RAÍZ DE /TOOLS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Organizar scripts
    scripts_moved = organize_scripts()
    
    # Ejecutar fix_script_paths.py
    if scripts_moved > 0:
        print_header("EJECUTANDO FIX_SCRIPT_PATHS.PY")
        run_fix_script_paths()
    
    # Reiniciar el servicio
    print_header("REINICIANDO EL SERVICIO")
    service_restarted = restart_service()
    
    print_header("ORGANIZACIÓN COMPLETADA")
    print(f"Se han categorizado {scripts_moved} scripts del directorio raíz")
    print(f"{'✅' if service_restarted else '❌'} El servicio edefrutos2025 se reinició {'correctamente' if service_restarted else 'con errores'}")
    
    if not service_restarted:
        print("\n⚠️ Se encontraron problemas que requieren atención:")
        print("  - El servicio edefrutos2025 no se reinició correctamente")
    else:
        print("\n✅ Todo funciona correctamente. Los scripts están organizados y son accesibles y ejecutables.")

if __name__ == "__main__":
    main()
