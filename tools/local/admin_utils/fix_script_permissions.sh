#!/bin/bash
# Script para verificar y corregir los permisos de todos los scripts
# Creado: 17/05/2025

echo "=== VERIFICACIÓN Y CORRECCIÓN DE PERMISOS DE SCRIPTS ==="
echo "Fecha y hora: $(date)"

# Definir el directorio raíz (subir 3 niveles desde tools/local/admin_utils/)
ROOT_DIR="$(dirname "$0")/../../.."  # Directorio raíz del proyecto
SCRIPTS_DIR="$ROOT_DIR/scripts"
TOOLS_DIR="$ROOT_DIR/tools"
TESTS_DIR="$ROOT_DIR/tests"

echo "Directorio raíz detectado: $ROOT_DIR"
echo "Directorio scripts: $SCRIPTS_DIR"
echo "Directorio tools: $TOOLS_DIR"
echo "Directorio tests: $TESTS_DIR"

# Función para verificar y corregir permisos
fix_permissions() {
    local dir=$1
    local count=0
    local fixed=0
    
    echo "Verificando scripts en: $dir"
    
    # Verificar que el directorio existe
    if [ ! -d "$dir" ]; then
        echo "  ❌ Directorio no existe: $dir"
        return
    fi
    
    # Buscar solo archivos (no directorios) con extensiones .py y .sh
    while IFS= read -r -d '' script; do
        # Verificar que es un archivo regular (no directorio)
        if [ -f "$script" ]; then
            count=$((count + 1))
            
            # Verificar si el script tiene permisos de ejecución
            if [ ! -x "$script" ]; then
                echo "  🔧 Corrigiendo permisos: $(basename "$script")"
                chmod +x "$script"
                fixed=$((fixed + 1))
            fi
        fi
    done < <(find "$dir" -type f \( -name "*.py" -o -name "*.sh" \) -print0 2>/dev/null)
    
    echo "  ✅ Total de scripts encontrados: $count"
    echo "  🔧 Scripts con permisos corregidos: $fixed"
}

# Verificar y corregir permisos en los tres directorios principales
fix_permissions "$SCRIPTS_DIR"
fix_permissions "$TOOLS_DIR"
fix_permissions "$TESTS_DIR"

echo "=== VERIFICACIÓN COMPLETADA ==="
echo "Fecha y hora: $(date)"

exit 0
