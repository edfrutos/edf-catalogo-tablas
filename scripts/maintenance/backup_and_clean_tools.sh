#!/bin/bash
# Script para mover scripts prescindibles de /tools y subdirectorios a /tools/_backup_scripts/
# Así puedes limpiar el directorio sin perder nada importante.

# Comprobación de dependencias antes de limpiar
SCRIPT_DIR="$(dirname "$0")"
"$SCRIPT_DIR/check_tools_imports.sh"
if [ $? -ne 0 ]; then
  echo "¡Atención! Revisa los scripts requeridos antes de limpiar. Abortando limpieza."
  exit 1
fi

BACKUP_DIR="$SCRIPT_DIR/_backup_scripts"
mkdir -p "$BACKUP_DIR"

# Listado de carpetas de donde mover scripts prescindibles
target_dirs=(
  "test_scripts"
  "root"
  "admin_utils"
  "db_utils"
  "utils"
  "app_runners"
  "maintenance"
  "monitoring"
  "image_utils"
  "session_utils"
  "catalog_utils"
  "aws_utils"
)

# Scripts principales que NO se deben mover
keep_scripts=(
  "fix_script_paths.py"
  "cleanup_tools_directory.py"
  "migrate_scripts.py"
  "organize_root_scripts.py"
  "test_script_execution.py"
  "script_runner.py"
)

for dir in "${target_dirs[@]}"; do
  if [ -d "$dir" ]; then
    for file in "$dir"/*; do
      fname=$(basename "$file")
      # No mover carpetas ni scripts principales
      if [[ -f "$file" && ! " ${keep_scripts[@]} " =~ " $fname " ]]; then
        echo "Moviendo $file a $BACKUP_DIR/"
        mv "$file" "$BACKUP_DIR/"
      fi
    done
  fi
  # Si la carpeta queda vacía, la dejamos (por si hay __init__.py o estructura)
done

echo "Respaldo completado. Puedes revisar $BACKUP_DIR antes de borrar definitivamente." 