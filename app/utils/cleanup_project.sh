#!/bin/bash
# Script de limpieza completa
echo "Iniciando limpieza completa del proyecto..."

# Enlaces simbólicos
echo "Eliminando enlaces simbólicos..."
find /Users/edefrutos/edf_catalogotablas -type l -delete

# Archivos Python temporales
echo "Eliminando archivos __pycache__ y .pyc..."
find /Users/edefrutos/edf_catalogotablas -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /Users/edefrutos/edf_catalogotablas -name "*.pyc" -delete
find /Users/edefrutos/edf_catalogotablas -name "*.pyo" -delete

# Respaldos antiguos
echo "Eliminando respaldos antiguos (>7 días)..."
find /Users/edefrutos/edf_catalogotablas -name "*.bak" -mtime +7 -delete
find /Users/edefrutos/edf_catalogotablas -name "*.backup" -mtime +7 -delete
find /Users/edefrutos/edf_catalogotablas -name "*.back" -mtime +7 -delete
find /Users/edefrutos/edf_catalogotablas -name "*~" -mtime +7 -delete

# Archivos temporales
echo "Eliminando archivos temporales..."
find /Users/edefrutos/edf_catalogotablas -name "*.tmp" -delete
find /Users/edefrutos/edf_catalogotablas -name "*.temp" -delete
find /Users/edefrutos/edf_catalogotablas -name ".DS_Store" -delete
find /Users/edefrutos/edf_catalogotablas -name "Thumbs.db" -delete

# Directorios de cache
echo "Limpiando directorios de cache..."
rm -rf /Users/edefrutos/edf_catalogotablas/.pytest_cache
rm -rf /Users/edefrutos/edf_catalogotablas/.mypy_cache
rm -rf /Users/edefrutos/edf_catalogotablas/flask_session/*

echo "Limpieza completa finalizada."