#!/bin/bash
# Script de limpieza general para proyecto Flask edf_catalogotablas
# Uso: bash tools/clean_project.sh

set -e

# 1. Eliminar archivos temporales y de depuración
rm -f login_page_debug.html *.log logs/*.log || true

# 2. Limpiar archivos .pyc y carpetas __pycache__
find . -name '*.pyc' -delete
find . -name '__pycache__' -type d -exec rm -rf {} +

# 3. Eliminar outputs de pruebas PDF y HTML temporales
find . -type f \( -name '*.pdf' -o -name '*.html' \) \
  -not -path './docs/*' \
  -not -path './static/*' \
  -not -path './templates/*' \
  -not -path './app/static/*' \
  -not -path './app/templates/*' \
  -not -path './README.md' \
  -delete

# 4. Eliminar archivos de backup (~, .bak)
find . -type f \( -name '*~' -o -name '*.bak' \) -delete

# 5. Eliminar archivos de pruebas locales o legacy ignorados
rm -f dev_template/tests/legacy/config_debug.py || true

# 6. Mostrar resumen de archivos sin seguimiento tras limpieza
echo -e "\nArchivos sin seguimiento tras limpieza:\n"
git status --short

echo -e "\nLimpieza completada. Revisa los archivos listados arriba antes de hacer commit."
