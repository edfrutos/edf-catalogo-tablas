#!/bin/bash

# Script para organizar archivos duplicados y temporales
# Crea una copia de seguridad antes de mover archivos

echo "=== Iniciando organización de archivos ==="

# 1. Crear estructura de carpetas de respaldo
mkdir -p backup_tmp/duplicate_scripts
mkdir -p backup_tmp/temp_files
mkdir -p backup_tmp/logs

# 2. Mover archivos duplicados
# Mover scripts duplicados de tools/
echo "Moviendo scripts duplicados..."
mv tools/crear_imagen_perfil_default.py backup_tmp/duplicate_scripts/ 2>/dev/null || echo "No se encontró crear_imagen_perfil_default.py"
mv tools/clean_images.py backup_tmp/duplicate_scripts/ 2>/dev/null || echo "No se encontró clean_images.py"
mv tools/cleanup_duplicates.py backup_tmp/duplicate_scripts/ 2>/dev/null || echo "No se encontró cleanup_duplicates.py"

# 3. Mover archivos temporales
echo "Moviendo archivos temporales..."
mv *.swp backup_tmp/temp_files/ 2>/dev/null || echo "No se encontraron archivos .swp"
mv *.swo backup_tmp/temp_files/ 2>/dev/null || echo "No se encontraron archivos .swo"
mv *~ backup_tmp/temp_files/ 2>/dev/null || echo "No se encontraron archivos temporales"

# 4. Mover logs antiguos
echo "Moviendo logs antiguos..."
mv logs/*.log backup_tmp/logs/ 2>/dev/null || echo "No se encontraron logs para mover"

# 5. Limpiar carpetas vacías
echo "Limpiando carpetas vacías..."
find . -type d -empty -delete 2>/dev/null

echo "=== Organización completada ==="
echo "Los archivos se han movido a la carpeta backup_tmp/"
echo "Revisa los cambios con 'git status' antes de hacer commit"
