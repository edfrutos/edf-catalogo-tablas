#!/bin/bash
# Script para verificar y corregir los permisos de todos los scripts
# Creado: 17/05/2025

echo "=== VERIFICACIÓN Y CORRECCIÓN DE PERMISOS DE SCRIPTS ==="
echo "Fecha y hora: $(date)"

# Definir el directorio raíz
ROOT_DIR="$(dirname "$0")/../.."  # Directorio raíz del proyecto
SCRIPTS_DIR="$ROOT_DIR/scripts"
TOOLS_DIR="$ROOT_DIR/tools"

# Función para verificar y corregir permisos
fix_permissions() {
    local dir=$1
    local count=0
    local fixed=0
    
    echo "Verificando scripts en: $dir"
    
    # Buscar todos los scripts Python y Shell
    for script in $(find "$dir" -type f -name "*.py" -o -name "*.sh"); do
        count=$((count + 1))
        
        # Verificar si el script tiene permisos de ejecución
        if [ ! -x "$script" ]; then
            echo "  Corrigiendo permisos: $script"
            chmod +x "$script"
            fixed=$((fixed + 1))
        fi
    done
    
    echo "  Total de scripts encontrados: $count"
    echo "  Scripts con permisos corregidos: $fixed"
}

# Verificar y corregir permisos en los directorios principales
fix_permissions "$SCRIPTS_DIR"
fix_permissions "$TOOLS_DIR"

echo "=== VERIFICACIÓN COMPLETADA ==="
echo "Fecha y hora: $(date)"

exit 0
