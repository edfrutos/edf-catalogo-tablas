#!/usr/bin/env python3
# Script para migrar scripts del directorio /scripts a /tools
# Creado: 18/05/2025

import os
import sys
import shutil
import datetime
import subprocess

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
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

def migrate_scripts():
    """Migra scripts del directorio /scripts a /tools"""
    print(f"Migrando scripts de {SCRIPTS_DIR} a {TOOLS_DIR}...")
    
    # Asegurar que los subdirectorios existen en /tools
    subdirs = [
        'admin_utils',
        'app_runners',
        'aws_utils',
        'catalog_utils',
        'db_utils',
        'deployment',
        'image_utils',
        'maintenance',
        'monitoring',
        'session_utils',
        'system',
        'utils',
        'root'  # Para scripts en el directorio raíz
    ]
    
    for subdir in subdirs:
        ensure_directory(os.path.join(TOOLS_DIR, subdir))
    
    # Migrar scripts en subdirectorios
    scripts_migrated = 0
    for subdir in subdirs:
        source_dir = os.path.join(SCRIPTS_DIR, subdir)
        target_dir = os.path.join(TOOLS_DIR, subdir)
        
        if os.path.exists(source_dir) and os.path.isdir(source_dir):
            print(f"Migrando scripts de {subdir}...")
            
            # Listar archivos en el subdirectorio
            for item in os.listdir(source_dir):
                source_item = os.path.join(source_dir, item)
                target_item = os.path.join(target_dir, item)
                
                # Solo migrar archivos, no directorios
                if os.path.isfile(source_item):
                    # Verificar si el archivo ya existe en el destino
                    if os.path.exists(target_item):
                        print(f"  ⚠️ El archivo ya existe en el destino: {target_item}")
                        continue
                    
                    # Copiar el archivo
                    shutil.copy2(source_item, target_item)
                    print(f"  ✅ Archivo migrado: {item}")
                    scripts_migrated += 1
    
    # Migrar scripts en el directorio raíz
    root_target_dir = os.path.join(TOOLS_DIR, 'root')
    for item in os.listdir(SCRIPTS_DIR):
        source_item = os.path.join(SCRIPTS_DIR, item)
        
        # Solo migrar archivos, no directorios
        if os.path.isfile(source_item):
            target_item = os.path.join(root_target_dir, item)
            
            # Verificar si el archivo ya existe en el destino
            if os.path.exists(target_item):
                print(f"  ⚠️ El archivo ya existe en el destino: {target_item}")
                continue
            
            # Copiar el archivo
            shutil.copy2(source_item, target_item)
            print(f"  ✅ Archivo migrado: {item}")
            scripts_migrated += 1
    
    return scripts_migrated

def categorize_scripts():
    """Categoriza scripts en /tools según su función"""
    print("Categorizando scripts en /tools...")
    
    # Definir categorías y patrones de nombres de archivos
    categories = {
        'admin_utils': ['admin', 'user', 'permission', 'role'],
        'db_utils': ['db', 'mongo', 'database', 'collection', 'catalog'],
        'maintenance': ['maintenance', 'backup', 'clean', 'update', 'monitor', 'supervise', 'start', 'stop', 'restart'],
        'monitoring': ['monitor', 'check', 'diagnose', 'log', 'status', 'health'],
        'aws_utils': ['aws', 's3', 'bucket', 'cloud'],
        'image_utils': ['image', 'photo', 'picture', 'thumbnail'],
        'session_utils': ['session', 'cookie', 'auth', 'login'],
        'system': ['system', 'os', 'process', 'service', 'daemon'],
        'utils': ['util', 'helper', 'tool']
    }
    
    # Listar todos los scripts en el directorio raíz de /tools
    scripts_moved = 0
    for item in os.listdir(TOOLS_DIR):
        source_item = os.path.join(TOOLS_DIR, item)
        
        # Solo procesar archivos, no directorios
        if os.path.isfile(source_item) and (item.endswith('.py') or item.endswith('.sh')):
            # Ignorar archivos específicos que deben permanecer en el directorio raíz
            if item in ['script_runner.py', 'fix_script_paths.py', 'migrate_scripts.py', '__init__.py']:
                continue
            
            # Determinar la categoría del script
            category = None
            for cat, patterns in categories.items():
                for pattern in patterns:
                    if pattern in item.lower():
                        category = cat
                        break
                if category:
                    break
            
            # Si no se encontró una categoría, usar 'utils'
            if not category:
                category = 'utils'
            
            # Mover el script a su categoría
            target_dir = os.path.join(TOOLS_DIR, category)
            ensure_directory(target_dir)
            
            target_item = os.path.join(target_dir, item)
            
            # Verificar si el archivo ya existe en el destino
            if os.path.exists(target_item):
                print(f"  ⚠️ El archivo ya existe en el destino: {target_item}")
                continue
            
            # Mover el archivo
            shutil.move(source_item, target_item)
            print(f"  ✅ Archivo categorizado: {item} -> {category}")
            scripts_moved += 1
    
    return scripts_moved

def run_fix_script_paths():
    """Ejecuta el script fix_script_paths.py"""
    print("Ejecutando fix_script_paths.py...")
    
    fix_script = os.path.join(TOOLS_DIR, 'fix_script_paths.py')
    if not os.path.exists(fix_script):
        print(f"❌ No se encontró el script {fix_script}")
        return False
    
    try:
        result = subprocess.run([fix_script], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ fix_script_paths.py ejecutado correctamente")
            return True
        else:
            print(f"❌ Error al ejecutar fix_script_paths.py: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error al ejecutar fix_script_paths.py: {str(e)}")
        return False

def main():
    print_header("MIGRACIÓN DE SCRIPTS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Migrar scripts
    print_header("MIGRANDO SCRIPTS")
    scripts_migrated = migrate_scripts()
    print(f"Se migraron {scripts_migrated} scripts")
    
    # Categorizar scripts
    print_header("CATEGORIZANDO SCRIPTS")
    scripts_moved = categorize_scripts()
    print(f"Se categorizaron {scripts_moved} scripts")
    
    # Ejecutar fix_script_paths.py
    print_header("EJECUTANDO FIX_SCRIPT_PATHS.PY")
    run_fix_script_paths()
    
    print_header("MIGRACIÓN COMPLETADA")
    print("Se han realizado las siguientes acciones:")
    print(f"1. Se migraron {scripts_migrated} scripts de /scripts a /tools")
    print(f"2. Se categorizaron {scripts_moved} scripts según su función")
    print("3. Se ejecutó fix_script_paths.py para crear enlaces simbólicos")
    print("\nLos scripts ahora están organizados en subdirectorios según su categoría.")

if __name__ == "__main__":
    main()
