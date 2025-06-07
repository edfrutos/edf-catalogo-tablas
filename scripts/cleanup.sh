#!/bin/bash

# Script de limpieza segura
# Crea una copia de seguridad antes de realizar cambios

echo "=== Iniciando limpieza segura ==="

# 1. Eliminar archivos compilados de Python
echo "Limpiando archivos compilados..."
find . -type f -name "*.py[co]" -delete
find . -type d -name "__pycache__" -exec rm -r {} +

# 2. Eliminar archivos temporales
echo "Limpiando archivos temporales..."
find . -type f -name "*~" -delete
find . -type f -name "*.swp" -delete
find . -type f -name "*.swo" -delete
find . -type f -name "*.bak" -delete

# 3. Eliminar archivos duplicados (manteniendo la versión en app/)
echo "Limpiando archivos duplicados..."
rm -f tools/crear_imagen_perfil_default.py
rm -f tools/clean_images.py
rm -f tools/cleanup_duplicates.py

# 4. Limpiar carpetas temporales
echo "Limpiando carpetas temporales..."
rm -rf temp_files_to_remove/
rm -rf __pycache__/
rm -rf .pytest_cache/

echo "=== Limpieza completada ==="
echo "Revisa los cambios con 'git status' antes de hacer commit"
