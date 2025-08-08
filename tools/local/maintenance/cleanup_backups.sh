#!/bin/bash
# Script para limpiar archivos de respaldo y temporales
# Creado: 19/05/2025

echo "=== INICIANDO LIMPIEZA DE ARCHIVOS DE RESPALDO ==="
echo "Fecha y hora: $(date)"

# Directorio raíz
ROOT_DIR="$(dirname "$0")/../.."  # Directorio raíz del proyecto

# Función para conservar el backup más reciente y eliminar el resto
cleanup_backups() {
    local pattern=$1
    local desc=$2
    
    echo ""
    echo "Limpiando $desc..."
    
    # Encontrar todos los archivos que coincidan con el patrón
    files=$(find $ROOT_DIR -name "$pattern" | sort)
    
    # Contar archivos
    total=$(echo "$files" | wc -l)
    
    if [ $total -eq 0 ]; then
        echo "  No se encontraron archivos de tipo $pattern."
        return
    fi
    
    # Obtener el archivo más reciente
    newest=$(echo "$files" | tail -n 1)
    
    echo "  Total de archivos encontrados: $total"
    echo "  Conservando el más reciente: $(basename "$newest")"
    
    # Eliminar todos excepto el más reciente
    for file in $files; do
        if [ "$file" != "$newest" ]; then
            echo "  Eliminando: $(basename "$file")"
            rm -f "$file"
        fi
    done
}

# Limpiar archivos de respaldo por tipo
cleanup_backups "app.py.bak.*" "respaldos de app.py"
cleanup_backups ".env.bak.*" "respaldos de .env"
cleanup_backups "app/routes/scripts_routes.py.bak.*" "respaldos de scripts_routes.py"
cleanup_backups "*.bak" "otros archivos .bak"

# Verificar el directorio de archivos temporales
echo ""
echo "Verificando directorio de archivos temporales..."

TEMP_DIR="$ROOT_DIR/temp_files_to_remove"

if [ -d "$TEMP_DIR" ]; then
    file_count=$(find "$TEMP_DIR" -type f | wc -l)
    echo "  El directorio $TEMP_DIR contiene $file_count archivos."
    
    # Preguntar antes de eliminar
    echo "  Nota: Para eliminar este directorio y su contenido, ejecute:"
    echo "  rm -rf $TEMP_DIR"
    echo "  ⚠️ Asegúrese de que no hay archivos importantes antes de ejecutar este comando."
else
    echo "  El directorio $TEMP_DIR no existe."
fi

echo ""
echo "=== LIMPIEZA COMPLETADA ==="
echo "Fecha y hora: $(date)"

exit 0
