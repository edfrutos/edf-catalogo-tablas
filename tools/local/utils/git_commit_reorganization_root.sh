#!/bin/bash
# Script para agregar los archivos reorganizados al control de versiones git
# Creado: 19/05/2025

echo "=== PREPARANDO CAMBIOS PARA COMMIT DE REORGANIZACIÓN ==="
echo "Fecha y hora: $(date)"

# Directorio raíz
ROOT_DIR="$(dirname "$0")/.."  # Directorio raíz del proyecto
cd "$ROOT_DIR"

# Paso 1: Agregar los cambios en app.py (comentarios de rutas)
echo ""
echo "1. Agregando cambios en app.py..."
git add app.py

# Paso 2: Agregar los archivos en /tools (scripts reorganizados)
echo ""
echo "2. Agregando scripts reorganizados en /tools..."
git add tools/

# Paso 3: Eliminar las referencias a scripts eliminados
echo ""
echo "3. Eliminando referencias a scripts antiguos..."
git rm -r --cached scripts/ 2>/dev/null || true

# Paso 4: Agregar otros archivos críticos modificados
echo ""
echo "4. Agregando otros archivos críticos modificados..."
git add wsgi.py gunicorn_config.py

echo ""
echo "=== PREPARACIÓN COMPLETADA ==="
echo "Los cambios están listos para commit."
echo "Ejecute el siguiente comando para hacer el commit:"
echo "git commit -m \"refactor: Reorganización de scripts y estructura del proyecto\""
echo ""
echo "Fecha y hora de finalización: $(date)"

exit 0
