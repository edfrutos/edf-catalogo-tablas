#!/bin/bash

# Script específico para resolver el conflicto del directorio tools en PyInstaller
# Autor: EDF Developer - 2025

echo "🔧 Resolviendo conflicto específico de PyInstaller con directorio 'tools'..."

# Función para verificar y limpiar conflictos específicos
clean_tools_conflicts() {
    local base_dir="$1"
    local cleaned=false
    
    echo "🔍 Verificando en: $base_dir"
    
    # Verificar si existe un archivo llamado 'tools' que podría conflictuar
    if [ -f "$base_dir/tools" ]; then
        echo "⚠️  Eliminando archivo conflictivo: $base_dir/tools"
        rm -f "$base_dir/tools"
        cleaned=true
    fi
    
    # Verificar en subdirectorios específicos de PyInstaller
    if [ -d "$base_dir/EDF_CatalogoDeTablas.app" ]; then
        local frameworks_dir="$base_dir/EDF_CatalogoDeTablas.app/Contents/Frameworks"
        if [ -d "$frameworks_dir" ]; then
            if [ -f "$frameworks_dir/tools" ]; then
                echo "⚠️  Eliminando archivo conflictivo en Frameworks: $frameworks_dir/tools"
                rm -f "$frameworks_dir/tools"
                cleaned=true
            fi
        fi
    fi
    
    return $([ "$cleaned" = true ] && echo 0 || echo 1)
}

# Limpiar completamente el entorno de build
echo "🧹 Limpieza completa del entorno de build..."
./clean_build.sh

# Verificar y limpiar conflictos específicos en directorios comunes
conflicts_found=false

# Verificar en el directorio actual
if clean_tools_conflicts "."; then
    conflicts_found=true
fi

# Verificar en dist si existe
if [ -d "dist" ]; then
    if clean_tools_conflicts "dist"; then
        conflicts_found=true
    fi
fi

# Verificar en build si existe
if [ -d "build" ]; then
    if clean_tools_conflicts "build"; then
        conflicts_found=true
    fi
fi

# Verificar en directorios temporales de PyInstaller
pyinstaller_cache="$HOME/Library/Application Support/pyinstaller"
if [ -d "$pyinstaller_cache" ]; then
    echo "🧹 Limpiando caché de PyInstaller..."
    rm -rf "$pyinstaller_cache"/*
fi

# Verificar si hay archivos .spec residuales
if [ -f "EDF_CatalogoDeTablas.spec" ]; then
    echo "🗑️ Eliminando archivo .spec residual..."
    rm -f EDF_CatalogoDeTablas.spec
fi

if [ "$conflicts_found" = true ]; then
    echo ""
    echo "✅ Conflictos de 'tools' resueltos"
else
    echo ""
    echo "✅ No se encontraron conflictos específicos de 'tools'"
fi

echo ""
echo "📋 Estado del entorno:"
echo "   - Directorio actual: $(pwd)"
echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
echo "   - Caché PyInstaller: $([ -d "$pyinstaller_cache" ] && echo "EXISTE" || echo "NO EXISTE")"

echo ""
echo "🚀 Ahora puedes ejecutar el build sin conflictos de 'tools'"
