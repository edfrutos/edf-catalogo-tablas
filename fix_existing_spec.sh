#!/bin/bash

# Script para modificar el archivo .spec existente y cambiar app_tools por app_utils
# Solución directa para el conflicto de PyInstaller
# Autor: EDF Developer - 2025

set -e

echo "🔧 MODIFICANDO ARCHIVO .SPEC EXISTENTE..."

# Función para modificar el archivo .spec
fix_existing_spec() {
    echo "📄 Modificando EDF_CatalogoDeTablas.spec existente..."
    
    if [ ! -f "EDF_CatalogoDeTablas.spec" ]; then
        echo "❌ Error: No se encuentra EDF_CatalogoDeTablas.spec"
        return 1
    fi
    
    # Hacer backup del archivo original
    cp EDF_CatalogoDeTablas.spec EDF_CatalogoDeTablas.spec.backup
    echo "📋 Backup creado: EDF_CatalogoDeTablas.spec.backup"
    
    # Reemplazar todas las ocurrencias de 'app_tools' por 'app_utils'
    echo "🔄 Reemplazando 'app_tools' por 'app_utils'..."
    sed -i '' 's/app_tools/app_utils/g' EDF_CatalogoDeTablas.spec
    
    echo "✅ Archivo .spec modificado exitosamente"
}

# Función para verificar los cambios
verify_changes() {
    echo "🔍 Verificando cambios realizados..."
    
    if [ ! -f "EDF_CatalogoDeTablas.spec" ]; then
        echo "❌ Error: No se encuentra el archivo .spec"
        return 1
    fi
    
    # Verificar que no hay referencias a 'app_tools'
    if grep -q "app_tools" EDF_CatalogoDeTablas.spec; then
        echo "❌ Error: Aún existen referencias a 'app_tools'"
        return 1
    else
        echo "✅ No hay referencias a 'app_tools'"
    fi
    
    # Verificar que se usan 'app_utils'
    if grep -q "app_utils" EDF_CatalogoDeTablas.spec; then
        echo "✅ Se usan referencias seguras a 'app_utils'"
    else
        echo "❌ Error: No se encontraron referencias a 'app_utils'"
        return 1
    fi
    
    # Mostrar algunas líneas modificadas
    echo "📋 Líneas modificadas (primeras 5):"
    grep -n "app_utils" EDF_CatalogoDeTablas.spec | head -5
    
    echo "✅ Verificación completada"
    return 0
}

# Función para mostrar información del cambio
show_change_info() {
    echo ""
    echo "📋 INFORMACIÓN DEL CAMBIO:"
    echo "   🔧 CAMBIO REALIZADO: Se cambió 'app_tools' por 'app_utils'"
    echo "   🎯 OBJETIVO: Evitar conflicto con el directorio 'tools'"
    echo "   📁 ANTES: tools/ → app_tools/"
    echo "   📁 AHORA: tools/ → app_utils/"
    echo "   ✅ BENEFICIO: No hay conflicto de nombres"
    echo "   📋 BACKUP: EDF_CatalogoDeTablas.spec.backup"
    echo ""
}

# Función principal
main() {
    echo "🚀 Modificando archivo .spec existente para evitar conflictos..."
    
    fix_existing_spec
    show_change_info
    
    if verify_changes; then
        echo "✅ Archivo .spec modificado y verificado correctamente"
        echo "💡 Ahora puedes ejecutar el build sin conflictos"
        echo "🚀 Comando recomendado: python -m PyInstaller EDF_CatalogoDeTablas.spec"
    else
        echo "❌ Error: No se pudo modificar o verificar el archivo .spec"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
