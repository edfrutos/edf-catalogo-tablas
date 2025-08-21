#!/bin/bash

# Script de diagnóstico para conflictos de PyInstaller
# Ayuda a identificar y analizar problemas específicos
# Autor: EDF Developer - 2025

set -e

echo "🔍 DIAGNÓSTICO: Analizando conflictos de PyInstaller..."

# Función para mostrar información del sistema
show_system_info() {
    echo "📋 INFORMACIÓN DEL SISTEMA:"
    echo "   - Sistema operativo: $(uname -s)"
    echo "   - Arquitectura: $(uname -m)"
    echo "   - Directorio actual: $(pwd)"
    echo "   - Usuario: $(whoami)"
    echo "   - Python: $(python --version 2>&1 || echo "NO INSTALADO")"
    echo "   - PyInstaller: $(pyinstaller --version 2>&1 || echo "NO INSTALADO")"
    echo ""
}

# Función para analizar la estructura del proyecto
analyze_project_structure() {
    echo "📁 ANÁLISIS DE ESTRUCTURA DEL PROYECTO:"
    
    # Verificar directorio tools
    if [ -d "tools" ]; then
        echo "   ✅ Directorio 'tools' existe"
        echo "   📏 Tamaño: $(du -sh tools 2>/dev/null | cut -f1 || echo "N/A")"
        echo "   📊 Elementos: $(find tools -type f | wc -l | tr -d ' ') archivos, $(find tools -type d | wc -l | tr -d ' ') directorios"
    else
        echo "   ❌ Directorio 'tools' NO existe"
    fi
    
    # Verificar si existe un archivo llamado 'tools'
    if [ -f "tools" ]; then
        echo "   ⚠️  ARCHIVO 'tools' existe (CONFLICTO POTENCIAL)"
        echo "   📏 Tamaño: $(du -sh tools 2>/dev/null | cut -f1 || echo "N/A")"
        echo "   📄 Tipo: $(file tools 2>/dev/null || echo "N/A")"
    else
        echo "   ✅ No hay archivo 'tools' conflictivo"
    fi
    
    # Verificar directorios de build
    if [ -d "dist" ]; then
        echo "   📁 Directorio 'dist' existe"
        echo "   📏 Tamaño: $(du -sh dist 2>/dev/null | cut -f1 || echo "N/A")"
    else
        echo "   ✅ Directorio 'dist' no existe"
    fi
    
    if [ -d "build" ]; then
        echo "   📁 Directorio 'build' existe"
        echo "   📏 Tamaño: $(du -sh build 2>/dev/null | cut -f1 || echo "N/A")"
    else
        echo "   ✅ Directorio 'build' no existe"
    fi
    
    echo ""
}

# Función para buscar archivos conflictivos
find_conflict_files() {
    echo "🔍 BUSCANDO ARCHIVOS CONFLICTIVOS:"
    
    # Buscar archivos llamados 'tools'
    echo "   🔍 Archivos llamados 'tools':"
    find . -name "tools" -type f 2>/dev/null | while read -r file; do
        echo "      📄 $file ($(du -sh "$file" 2>/dev/null | cut -f1 || echo "N/A"))"
    done
    
    # Buscar en directorios específicos de PyInstaller
    if [ -d "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks" ]; then
        echo "   🔍 En Frameworks de PyInstaller:"
        find dist/EDF_CatalogoDeTablas.app/Contents/Frameworks -name "tools" 2>/dev/null | while read -r file; do
            echo "      📄 $file ($(du -sh "$file" 2>/dev/null | cut -f1 || echo "N/A"))"
        done
    fi
    
    echo ""
}

# Función para analizar archivos .spec
analyze_spec_files() {
    echo "📄 ANÁLISIS DE ARCHIVOS .SPEC:"
    
    if ls *.spec 1> /dev/null 2>&1; then
        for spec_file in *.spec; do
            echo "   📄 $spec_file:"
            echo "      📏 Tamaño: $(du -sh "$spec_file" 2>/dev/null | cut -f1 || echo "N/A")"
            echo "      📊 Líneas: $(wc -l < "$spec_file" 2>/dev/null || echo "N/A")"
            
            # Buscar referencias a 'tools' en el archivo .spec
            if grep -q "tools" "$spec_file" 2>/dev/null; then
                echo "      🔍 Referencias a 'tools' encontradas:"
                grep -n "tools" "$spec_file" 2>/dev/null | head -5 | while read -r line; do
                    echo "         $line"
                done
            else
                echo "      ✅ No hay referencias a 'tools'"
            fi
        done
    else
        echo "   ✅ No hay archivos .spec"
    fi
    
    echo ""
}

# Función para verificar permisos
check_permissions() {
    echo "🔐 VERIFICACIÓN DE PERMISOS:"
    
    # Verificar permisos del directorio tools
    if [ -d "tools" ]; then
        echo "   📁 Permisos de 'tools': $(ls -ld tools 2>/dev/null | awk '{print $1}' || echo "N/A")"
    fi
    
    # Verificar permisos de archivos importantes
    for file in "run_server.py" "config.py" "requirements_python310.txt"; do
        if [ -f "$file" ]; then
            echo "   📄 Permisos de '$file': $(ls -l "$file" 2>/dev/null | awk '{print $1}' || echo "N/A")"
        fi
    done
    
    echo ""
}

# Función para mostrar recomendaciones
show_recommendations() {
    echo "💡 RECOMENDACIONES:"
    
    # Verificar si hay archivos conflictivos
    if [ -f "tools" ]; then
        echo "   ❌ PROBLEMA DETECTADO: Existe un archivo 'tools' conflictivo"
        echo "   🔧 SOLUCIÓN: Eliminar el archivo con: rm -f tools"
    fi
    
    if find . -name "tools" -type f 2>/dev/null | grep -q .; then
        echo "   ❌ PROBLEMA DETECTADO: Existen archivos 'tools' conflictivos en el proyecto"
        echo "   🔧 SOLUCIÓN: Eliminar con: find . -name 'tools' -type f -delete"
    fi
    
    if [ ! -d "tools" ]; then
        echo "   ❌ PROBLEMA DETECTADO: No existe el directorio 'tools'"
        echo "   🔧 SOLUCIÓN: Crear el directorio o restaurar desde git"
    fi
    
    # Verificar si hay directorios de build
    if [ -d "dist" ] || [ -d "build" ]; then
        echo "   ⚠️  ADVERTENCIA: Existen directorios de build"
        echo "   🔧 RECOMENDACIÓN: Limpiar con: rm -rf dist/ build/"
    fi
    
    # Verificar archivos .spec
    if ls *.spec 1> /dev/null 2>&1; then
        echo "   ⚠️  ADVERTENCIA: Existen archivos .spec"
        echo "   🔧 RECOMENDACIÓN: Eliminar con: rm -f *.spec"
    fi
    
    echo ""
    echo "   🚀 COMANDOS RECOMENDADOS:"
    echo "      ./pre_build_cleanup.sh    # Limpieza completa"
    echo "      ./verify_build_environment.sh    # Verificar entorno"
    echo "      ./build_macos_app.sh      # Build con script mejorado"
    echo ""
}

# Función principal
main() {
    echo "🚀 Iniciando diagnóstico de conflictos de PyInstaller..."
    echo ""
    
    show_system_info
    analyze_project_structure
    find_conflict_files
    analyze_spec_files
    check_permissions
    show_recommendations
    
    echo "✅ Diagnóstico completado"
    echo "💡 Revisa las recomendaciones arriba para resolver problemas"
}

# Ejecutar función principal
main "$@"
