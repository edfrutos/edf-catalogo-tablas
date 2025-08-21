#!/bin/bash

# Script para limpiar completamente el entorno de build
# Autor: EDF Developer - 2025

echo "🧹 Limpieza completa del entorno de build..."

# Eliminar directorios de build
echo "📁 Eliminando directorios de build..."
rm -rf build/
rm -rf dist/
rm -rf __pycache__/
rm -rf .pytest_cache/

# Eliminar archivos .spec
echo "📄 Eliminando archivos .spec..."
rm -f *.spec

# Eliminar archivos Python compilados
echo "🐍 Eliminando archivos Python compilados..."
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete

# Eliminar directorios __pycache__
echo "🗂️ Eliminando directorios __pycache__..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Eliminar archivos temporales de macOS
echo "🍎 Eliminando archivos temporales de macOS..."
find . -name ".DS_Store" -delete
find . -name "*.swp" -delete
find . -name "*.swo" -delete

# Eliminar archivos de IDE
echo "💻 Eliminando archivos de IDE..."
find . -name "*.vscode" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".idea" -type d -exec rm -rf {} + 2>/dev/null || true

# Verificar que no hay archivos conflictivos en dist
if [ -d "dist" ]; then
    echo "⚠️  Eliminando directorio dist residual..."
    rm -rf dist/
fi

echo "✅ Limpieza completada!"
echo "🚀 Ahora puedes ejecutar el build sin conflictos."
