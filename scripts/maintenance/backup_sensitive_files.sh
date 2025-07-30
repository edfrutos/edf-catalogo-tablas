#!/bin/bash
# Script para respaldar archivos sensibles listados en .gitignore
# Guarda los archivos en la carpeta ./sensitive_backup con la misma estructura relativa
# Uso: bash tools/backup_sensitive_files.sh

BACKUP_DIR="sensitive_backup"
mkdir -p "$BACKUP_DIR"

# Lista blanca de patrones sensibles a respaldar (ajusta según tu proyecto)
PATTERNS=(
  ".env"
  ".env.*"
  "*.env"
  "*apikey*"
  "*password*"
  "*token*"
  "*secret*"
  "*credentials*"
  "dev_template/tests/legacy/config_debug.py"
)

BACKED_UP=()
for PATTERN in "${PATTERNS[@]}"; do
  # Buscar archivos que coincidan con el patrón (evitar duplicados y omitir backup dir)
  find . -path "./$BACKUP_DIR" -prune -o -type f -name "${PATTERN}" -print | while read -r FILE; do
    # Evitar duplicados
    [[ " ${BACKED_UP[*]} " == *" $FILE "* ]] && continue
    DEST="$BACKUP_DIR/${FILE#./}"
    mkdir -p "$(dirname "$DEST")"
    cp "$FILE" "$DEST"
    BACKED_UP+=("$FILE")
    echo "Resguardado: $FILE -> $DEST"
  done
done

echo -e "\nRespaldo completado en ./$BACKUP_DIR. Total archivos respaldados: ${#BACKED_UP[@]}"
