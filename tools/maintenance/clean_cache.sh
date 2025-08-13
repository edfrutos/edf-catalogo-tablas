#!/bin/bash
# Script para limpiar caches de Python
# Uso: ./clean_cache.sh

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Limpiando caches de Python ==="
echo "Directorio de trabajo: $SCRIPT_DIR"
echo ""

# Función para mostrar progreso
show_progress() {
    echo "[$1] $2"
}

# Contar archivos antes de la limpieza
show_progress "INFO" "Contando archivos de cache existentes..."
PYCACHE_DIRS=$(find . -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')
PYC_FILES=$(find . -name '*.pyc' -type f 2>/dev/null | wc -l | tr -d ' ')
PYO_FILES=$(find . -name '*.pyo' -type f 2>/dev/null | wc -l | tr -d ' ')

echo "Encontrados:"
echo "  - Directorios __pycache__: $PYCACHE_DIRS"
echo "  - Archivos .pyc: $PYC_FILES"
echo "  - Archivos .pyo: $PYO_FILES"
echo ""

if [ "$PYCACHE_DIRS" -eq 0 ] && [ "$PYC_FILES" -eq 0 ] && [ "$PYO_FILES" -eq 0 ]; then
    show_progress "INFO" "No se encontraron archivos de cache para limpiar"
    exit 0
fi

# Limpiar directorio __pycache__ en la raíz si existe
if [ -d "__pycache__" ]; then
    show_progress "CLEAN" "Eliminando directorio __pycache__ en la raíz..."
    rm -rf __pycache__
fi

# Buscar y eliminar todos los directorios __pycache__
show_progress "CLEAN" "Eliminando directorios __pycache__ recursivamente..."
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null

# Eliminar archivos .pyc
show_progress "CLEAN" "Eliminando archivos .pyc..."
find . -name '*.pyc' -type f -delete 2>/dev/null

# Eliminar archivos .pyo (Python optimized)
show_progress "CLEAN" "Eliminando archivos .pyo..."
find . -name '*.pyo' -type f -delete 2>/dev/null

# Eliminar archivos .pyd (Windows Python extensions) si existen
show_progress "CLEAN" "Eliminando archivos .pyd..."
find . -name '*.pyd' -type f -delete 2>/dev/null

# Limpiar directorios de pytest cache si existen
if [ -d ".pytest_cache" ]; then
    show_progress "CLEAN" "Eliminando .pytest_cache..."
    rm -rf .pytest_cache
fi

# Limpiar directorios de coverage si existen
if [ -d ".coverage" ]; then
    show_progress "CLEAN" "Eliminando .coverage..."
    rm -rf .coverage
fi

if [ -d "htmlcov" ]; then
    show_progress "CLEAN" "Eliminando htmlcov..."
    rm -rf htmlcov
fi

# Limpiar directorios de mypy cache si existen
if [ -d ".mypy_cache" ]; then
    show_progress "CLEAN" "Eliminando .mypy_cache..."
    rm -rf .mypy_cache
fi

# Verificar limpieza
echo ""
show_progress "CHECK" "Verificando limpieza..."
REMAINING_PYCACHE=$(find . -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')
REMAINING_PYC=$(find . -name '*.pyc' -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$REMAINING_PYCACHE" -eq 0 ] && [ "$REMAINING_PYC" -eq 0 ]; then
    show_progress "SUCCESS" "Limpieza completada exitosamente"
    echo "✅ Todos los archivos de cache han sido eliminados"
else
    show_progress "WARNING" "Algunos archivos no pudieron ser eliminados"
    echo "⚠️  Directorios __pycache__ restantes: $REMAINING_PYCACHE"
    echo "⚠️  Archivos .pyc restantes: $REMAINING_PYC"
fi

echo ""
echo "=== Limpieza finalizada ==="
