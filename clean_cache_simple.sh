#!/bin/bash
# Script simple para limpiar caches de Python
# Uso: ./clean_cache_simple.sh

echo "Limpiando caches de Python..."

# Comando original optimizado
rm -rf __pycache__ 2>/dev/null
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -type f -delete 2>/dev/null

echo "✅ Cache limpiado"
