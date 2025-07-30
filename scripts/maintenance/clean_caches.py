#!/usr/bin/env python3
"""
Script para limpiar todas las cachés del proyecto edf_catalogotablas.
Elimina:
- Todos los directorios __pycache__ (recursivamente)
- .pytest_cache
- app/cache_system.pyc y app/__pycache__/cache_system*
- flask_session (si existe)
- Otros directorios temporales de caché detectados
"""
import os
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

CACHE_DIRS = [
    '__pycache__',
    '.pytest_cache',
    'flask_session',
]


def remove_dir_recursively(base_dir, target_name):
    """Elimina todos los directorios con nombre target_name bajo base_dir."""
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d == target_name:
                dir_to_remove = os.path.join(root, d)
                print(f"Eliminando directorio: {dir_to_remove}")
                shutil.rmtree(dir_to_remove, ignore_errors=True)

def remove_file_if_exists(path):
    if os.path.isfile(path):
        print(f"Eliminando archivo: {path}")
        os.remove(path)

def clean_caches():
    print(f"Limpiando caches en {PROJECT_ROOT} ...")
    # Eliminar todos los __pycache__
    remove_dir_recursively(PROJECT_ROOT, '__pycache__')
    # Eliminar .pytest_cache
    pytest_cache = os.path.join(PROJECT_ROOT, '.pytest_cache')
    if os.path.isdir(pytest_cache):
        print(f"Eliminando directorio: {pytest_cache}")
        shutil.rmtree(pytest_cache, ignore_errors=True)
    # Eliminar flask_session
    flask_session = os.path.join(PROJECT_ROOT, 'flask_session')
    if os.path.isdir(flask_session):
        print(f"Eliminando directorio: {flask_session}")
        shutil.rmtree(flask_session, ignore_errors=True)
    # Eliminar pyc específicos
    cache_system_pyc = os.path.join(PROJECT_ROOT, 'app', '__pycache__', 'cache_system.cpython-310.pyc')
    remove_file_if_exists(cache_system_pyc)
    # Eliminar otros archivos pyc en app/__pycache__
    app_pycache = os.path.join(PROJECT_ROOT, 'app', '__pycache__')
    if os.path.isdir(app_pycache):
        for f in os.listdir(app_pycache):
            if f.endswith('.pyc'):
                remove_file_if_exists(os.path.join(app_pycache, f))
    print("Limpieza de caches completada.")

if __name__ == '__main__':
    clean_caches()
