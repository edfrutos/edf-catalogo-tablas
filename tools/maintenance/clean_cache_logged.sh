#!/bin/bash
# Script para limpiar caches con logging
# Uso: ./clean_cache_logged.sh

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Crear directorio de logs si no existe
mkdir -p logs

# Función para ejecutar con logging
run_with_log() {
    echo "=== Limpieza de cache $(date) ===" >> logs/cache_cleanup.log
    
    if [ -f "./logcmdpy.sh" ]; then
        # Usar el sistema de logging existente
        ./logcmdpy.sh bash -c "
            echo 'Iniciando limpieza de cache...'
            rm -rf __pycache__ 2>/dev/null && echo 'Eliminado __pycache__ raíz'
            find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null && echo 'Eliminados directorios __pycache__'
            find . -name '*.pyc' -type f -delete 2>/dev/null && echo 'Eliminados archivos .pyc'
            echo 'Limpieza de cache completada'
        "
    else
        # Logging manual si no existe logcmdpy.sh
        {
            echo "Iniciando limpieza de cache..."
            rm -rf __pycache__ 2>/dev/null && echo "Eliminado __pycache__ raíz"
            find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null && echo "Eliminados directorios __pycache__"
            find . -name '*.pyc' -type f -delete 2>/dev/null && echo "Eliminados archivos .pyc"
            echo "Limpieza de cache completada"
            echo "---"
        } | tee -a logs/cache_cleanup.log
    fi
}

run_with_log
