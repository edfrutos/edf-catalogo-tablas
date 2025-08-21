#!/bin/bash

# Script para detectar y corregir conflictos de PyInstaller
# Autor: EDF Developer - 2025

echo "🔍 Detectando conflictos de PyInstaller..."

# Función para verificar conflictos de directorios
check_conflicts() {
    local base_dir="$1"
    local conflict_found=false
    
    echo "🔍 Verificando en: $base_dir"
    
    # Buscar archivos que podrían conflictuar con directorios
    for item in "$base_dir"/*; do
        if [ -f "$item" ]; then
            local basename_item=$(basename "$item")
            if [ -d "$base_dir/$basename_item" ]; then
                echo "⚠️  CONFLICTO DETECTADO:"
                echo "   Archivo: $item"
                echo "   Directorio: $base_dir/$basename_item"
                echo "   Ambos existen con el mismo nombre"
                conflict_found=true
            fi
        fi
    done
    
    return $([ "$conflict_found" = true ] && echo 1 || echo 0)
}

# Verificar en directorios comunes de PyInstaller
conflicts_detected=false

# Verificar en el directorio actual
if check_conflicts "."; then
    conflicts_detected=true
fi

# Verificar en dist si existe
if [ -d "dist" ]; then
    if check_conflicts "dist"; then
        conflicts_detected=true
    fi
    
    # Verificar específicamente en la estructura de la app
    if [ -d "dist/EDF_CatalogoDeTablas.app" ]; then
        if check_conflicts "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks"; then
            conflicts_detected=true
        fi
    fi
fi

# Verificar en build si existe
if [ -d "build" ]; then
    if check_conflicts "build"; then
        conflicts_detected=true
    fi
fi

if [ "$conflicts_detected" = true ]; then
    echo ""
    echo "❌ CONFLICTOS DETECTADOS"
    echo "🔧 Ejecutando limpieza automática..."
    
    # Limpiar completamente
    ./clean_build.sh
    
    echo "✅ Limpieza completada"
    echo "🚀 Ahora puedes ejecutar el build sin conflictos"
else
    echo "✅ No se detectaron conflictos"
fi

echo ""
echo "📋 Resumen de verificación:"
echo "   - Directorio actual: $(pwd)"
echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
