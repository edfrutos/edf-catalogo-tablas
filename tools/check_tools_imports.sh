#!/bin/bash
# Script para buscar importaciones de scripts de tools en todo el proyecto
# y listar los scripts requeridos para no borrarlos accidentalmente.

# Directorio raíz del proyecto (ajusta si es necesario)
ROOT_DIR="$(dirname "$0")/.."

# Buscar importaciones de tools en todos los .py del proyecto
IMPORTS=$(grep -rE "from tools\\.|import tools\\." "$ROOT_DIR" --include='*.py' | grep -v 'venv' | grep -v 'site-packages')

if [ -z "$IMPORTS" ]; then
  echo "No se encontraron importaciones de scripts de tools en el proyecto."
  exit 0
fi

echo "==== SCRIPTS DE /tools REQUERIDOS POR LA APP ===="
# Extraer rutas de scripts importados
REQUIRED_SCRIPTS=$(echo "$IMPORTS" | grep -oE 'tools\.[a-zA-Z0-9_\.]+' | sed 's/\./\//g' | sed 's/$/.py/' | sort | uniq)

for script in $REQUIRED_SCRIPTS; do
  # Verifica si el archivo existe realmente
  if [ -f "$ROOT_DIR/$script" ]; then
    echo "$script (ENCONTRADO)"
  else
    echo "$script (NO ENCONTRADO - ¡Revisa dependencias!)"
  fi
done

echo "\nIMPORTACIONES DETECTADAS:"
echo "$IMPORTS" 