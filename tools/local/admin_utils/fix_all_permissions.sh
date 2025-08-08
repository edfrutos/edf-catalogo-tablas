#!/bin/bash

# Script para verificar y corregir permisos de archivos ejecutables
# Autor: Sistema de Administración
# Fecha: $(date)

echo "🔧 Verificando y corrigiendo permisos de archivos ejecutables..."
echo "================================================================"

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
echo "📁 Directorio raíz: $PROJECT_ROOT"
echo

# Función para contar archivos
count_files() {
    local dir="$1"
    local pattern="$2"
    if [ -d "$dir" ]; then
        find "$dir" -name "$pattern" 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

# Función para corregir permisos
fix_permissions() {
    local dir="$1"
    local pattern="$2"
    local description="$3"
    
    if [ -d "$dir" ]; then
        local count_before=$(count_files "$dir" "$pattern")
        find "$dir" -name "$pattern" -exec chmod +x {} \; 2>/dev/null
        local count_after=$(count_files "$dir" "$pattern")
        echo "✅ $description: $count_after archivos corregidos"
    else
        echo "⚠️  $description: Directorio no encontrado"
    fi
}

# Corregir permisos de archivos Python
echo "🐍 Corrigiendo permisos de archivos Python..."
fix_permissions "$PROJECT_ROOT/app/templates/dev_template/tests" "*.py" "Tests de dev_template"
fix_permissions "$PROJECT_ROOT/tests/local" "*.py" "Tests locales"
fix_permissions "$PROJECT_ROOT/tests/production" "*.py" "Tests de producción"
fix_permissions "$PROJECT_ROOT/tools/local" "*.py" "Herramientas locales"
fix_permissions "$PROJECT_ROOT/tools/production" "*.py" "Herramientas de producción"
fix_permissions "$PROJECT_ROOT/scripts/local" "*.py" "Scripts locales"
fix_permissions "$PROJECT_ROOT/scripts/production" "*.py" "Scripts de producción"
echo

# Corregir permisos de archivos Shell
echo "🐚 Corrigiendo permisos de archivos Shell..."
fix_permissions "$PROJECT_ROOT" "*.sh" "Scripts Shell en todo el proyecto"
echo

# Verificar permisos específicos
echo "🔍 Verificando permisos específicos..."
echo "----------------------------------------"

# Verificar archivo específico mencionado
SPECIFIC_FILE="$PROJECT_ROOT/app/templates/dev_template/tests/integration/test_admin_api.py"
if [ -f "$SPECIFIC_FILE" ]; then
    if [ -x "$SPECIFIC_FILE" ]; then
        echo "✅ $SPECIFIC_FILE: Permisos correctos"
    else
        echo "❌ $SPECIFIC_FILE: Sin permisos de ejecución"
        chmod +x "$SPECIFIC_FILE"
        echo "✅ Permisos corregidos"
    fi
else
    echo "⚠️  $SPECIFIC_FILE: Archivo no encontrado"
fi

# Verificar directorios principales
echo
echo "📊 Resumen de archivos ejecutables:"
echo "-----------------------------------"
echo "🐍 Archivos Python ejecutables:"
find "$PROJECT_ROOT" -name "*.py" -executable 2>/dev/null | wc -l | tr -d ' '
echo "🐚 Archivos Shell ejecutables:"
find "$PROJECT_ROOT" -name "*.sh" -executable 2>/dev/null | wc -l | tr -d ' '

echo
echo "🎉 Verificación de permisos completada!"
echo "========================================"
