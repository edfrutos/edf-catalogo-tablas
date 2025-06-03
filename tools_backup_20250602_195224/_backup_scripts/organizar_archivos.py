#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para organizar archivos de prueba y backup en el proyecto.
- Mueve los archivos de prueba al directorio /tests
- Mueve los archivos de backup al directorio /backups
"""

import os
import shutil
import re
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('organizar_archivos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directorios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(BASE_DIR, 'tests')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

# Asegurar que los directorios existen
os.makedirs(TESTS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

# Patrones para identificar archivos de prueba
TEST_PATTERNS = [
    r'^test_.*\.py$',
    r'^.*_test\.py$',
    r'^test\..*$',
    r'^.*\.test$',
    r'^.*test.*\.py$'
]

# Patrones para identificar archivos de backup
BACKUP_PATTERNS = [
    r'^.*\.bak$',
    r'^.*\.backup$',
    r'^.*\.old$',
    r'^.*\.back$',
    r'^.*_backup.*$',
    r'^backup_.*$',
    r'^.*_old$',
    r'^.*_copy.*$',
    r'^copy_of_.*$'
]

# Directorios a excluir de la búsqueda
EXCLUDE_DIRS = [
    '.git',
    '.venv',
    'venv',
    'env',
    'node_modules',
    'tests',
    'backups'
]

def is_test_file(filename):
    """Determina si un archivo es un archivo de prueba basado en su nombre."""
    for pattern in TEST_PATTERNS:
        if re.match(pattern, os.path.basename(filename)):
            return True
    return False

def is_backup_file(filename):
    """Determina si un archivo es un archivo de backup basado en su nombre."""
    for pattern in BACKUP_PATTERNS:
        if re.match(pattern, os.path.basename(filename)):
            return True
    return False

def should_exclude_dir(dirpath):
    """Determina si un directorio debe ser excluido de la búsqueda."""
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in dirpath.split(os.path.sep):
            return True
    return False

def organize_files():
    """Organiza los archivos de prueba y backup."""
    test_files_moved = 0
    backup_files_moved = 0
    errors = 0

    # Crear un timestamp para el informe
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Recorrer todos los archivos en el directorio base
    for root, dirs, files in os.walk(BASE_DIR):
        # Excluir directorios que no queremos procesar
        if should_exclude_dir(root):
            continue
        
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, BASE_DIR)
            
            try:
                # Procesar archivos de prueba
                if is_test_file(file):
                    # Crear la estructura de directorios en tests/
                    rel_dir = os.path.dirname(relpath)
                    target_dir = os.path.join(TESTS_DIR, rel_dir)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Mover el archivo
                    target_path = os.path.join(TESTS_DIR, relpath)
                    if not os.path.exists(target_path):
                        shutil.move(filepath, target_path)
                        logger.info(f"Archivo de prueba movido: {relpath} -> {target_path}")
                        test_files_moved += 1
                    else:
                        # Si ya existe, crear una copia con timestamp
                        filename, ext = os.path.splitext(file)
                        new_filename = f"{filename}_{timestamp}{ext}"
                        target_path = os.path.join(target_dir, new_filename)
                        shutil.copy2(filepath, target_path)
                        os.remove(filepath)
                        logger.info(f"Archivo de prueba duplicado, copiado con timestamp: {relpath} -> {target_path}")
                        test_files_moved += 1
                
                # Procesar archivos de backup
                elif is_backup_file(file):
                    # Crear la estructura de directorios en backups/
                    rel_dir = os.path.dirname(relpath)
                    target_dir = os.path.join(BACKUPS_DIR, rel_dir)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Mover el archivo
                    target_path = os.path.join(BACKUPS_DIR, relpath)
                    if not os.path.exists(target_path):
                        shutil.move(filepath, target_path)
                        logger.info(f"Archivo de backup movido: {relpath} -> {target_path}")
                        backup_files_moved += 1
                    else:
                        # Si ya existe, crear una copia con timestamp
                        filename, ext = os.path.splitext(file)
                        new_filename = f"{filename}_{timestamp}{ext}"
                        target_path = os.path.join(target_dir, new_filename)
                        shutil.copy2(filepath, target_path)
                        os.remove(filepath)
                        logger.info(f"Archivo de backup duplicado, copiado con timestamp: {relpath} -> {target_path}")
                        backup_files_moved += 1
            
            except Exception as e:
                logger.error(f"Error al procesar {relpath}: {str(e)}")
                errors += 1
    
    # Mostrar resumen
    logger.info(f"Organización completada:")
    logger.info(f"- Archivos de prueba movidos: {test_files_moved}")
    logger.info(f"- Archivos de backup movidos: {backup_files_moved}")
    logger.info(f"- Errores encontrados: {errors}")
    
    return {
        'test_files_moved': test_files_moved,
        'backup_files_moved': backup_files_moved,
        'errors': errors
    }

if __name__ == "__main__":
    print("Iniciando organización de archivos...")
    results = organize_files()
    print(f"\nResumen:")
    print(f"- Archivos de prueba movidos: {results['test_files_moved']}")
    print(f"- Archivos de backup movidos: {results['backup_files_moved']}")
    print(f"- Errores encontrados: {results['errors']}")
    print("\nProceso completado. Consulta el archivo 'organizar_archivos.log' para más detalles.")
