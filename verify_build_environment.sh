#!/bin/bash

# Script para verificar que el entorno está listo para el build
# Se ejecuta después de la limpieza para asegurar que no hay conflictos
# Autor: EDF Developer - 2025

set -e

echo "🔍 VERIFICACIÓN: Comprobando entorno para build..."

# Función para verificar el entorno básico
check_basic_environment() {
    echo "🔍 Verificando entorno básico..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "config.py" ]; then
        echo "❌ Error: No se encuentra config.py"
        exit 1
    fi
    
    # Verificar que existe el directorio tools
    if [ ! -d "tools" ]; then
        echo "❌ Error: No se encuentra el directorio tools"
        exit 1
    fi
    
    # Verificar que tools es un directorio, no un archivo
    if [ -f "tools" ]; then
        echo "❌ Error: 'tools' es un archivo, debe ser un directorio"
        exit 1
    fi
    
    echo "✅ Entorno básico verificado correctamente"
}

# Función para verificar que no hay conflictos
check_no_conflicts() {
    echo "🔍 Verificando ausencia de conflictos..."
    
    # Verificar que no hay archivos 'tools' conflictivos
    if [ -f "tools" ]; then
        echo "❌ Error: Existe un archivo 'tools' conflictivo en el directorio raíz"
        exit 1
    fi
    
    # Buscar archivos 'tools' conflictivos en todo el proyecto
    if find . -name "tools" -type f 2>/dev/null | grep -q .; then
        echo "❌ Error: Existen archivos 'tools' conflictivos en el proyecto:"
        find . -name "tools" -type f 2>/dev/null
        exit 1
    fi
    
    # Verificar que no hay directorios de build
    if [ -d "dist" ]; then
        echo "⚠️  Advertencia: El directorio 'dist' existe, pero no debería causar problemas"
    fi
    
    if [ -d "build" ]; then
        echo "⚠️  Advertencia: El directorio 'build' existe, pero no debería causar problemas"
    fi
    
    echo "✅ No se encontraron conflictos"
}

# Función para verificar dependencias
check_dependencies() {
    echo "🔍 Verificando dependencias..."
    
    # Verificar Python
    if ! command -v python &> /dev/null; then
        echo "❌ Error: Python no está instalado"
        exit 1
    fi
    
    # Verificar PyInstaller
    if ! command -v pyinstaller &> /dev/null; then
        echo "❌ Error: PyInstaller no está instalado"
        exit 1
    fi
    
    # Verificar archivo principal
    if [ ! -f "run_server.py" ]; then
        echo "❌ Error: No se encuentra run_server.py"
        exit 1
    fi
    
    echo "✅ Dependencias verificadas correctamente"
}

# Función para verificar estructura del proyecto
check_project_structure() {
    echo "🔍 Verificando estructura del proyecto..."
    
    # Verificar directorios importantes
    local required_dirs=("app" "tools" "config")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            echo "❌ Error: No se encuentra el directorio '$dir'"
            exit 1
        fi
    done
    
    # Verificar archivos importantes
    local required_files=("config.py" "run_server.py" "requirements_python310.txt")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ Error: No se encuentra el archivo '$file'"
            exit 1
        fi
    done
    
    echo "✅ Estructura del proyecto verificada correctamente"
}

# Función para mostrar estado final
show_verification_summary() {
    echo ""
    echo "📋 RESUMEN DE VERIFICACIÓN:"
    echo "   - Directorio actual: $(pwd)"
    echo "   - Python: $(command -v python &> /dev/null && echo "INSTALADO" || echo "NO INSTALADO")"
    echo "   - PyInstaller: $(command -v pyinstaller &> /dev/null && echo "INSTALADO" || echo "NO INSTALADO")"
    echo "   - Directorio tools: $([ -d "tools" ] && echo "EXISTE (DIRECTORIO)" || echo "NO EXISTE")"
    echo "   - Archivo tools: $([ -f "tools" ] && echo "EXISTE (ARCHIVO - PROBLEMA)" || echo "NO EXISTE")"
    echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
    
    echo ""
    echo "✅ VERIFICACIÓN COMPLETADA - El entorno está listo para el build"
}

# Función principal
main() {
    echo "🚀 Iniciando verificación del entorno para build..."
    
    check_basic_environment
    check_no_conflicts
    check_dependencies
    check_project_structure
    show_verification_summary
    
    echo ""
    echo "🎉 ¡El entorno está completamente verificado y listo para el build!"
    echo "💡 Puedes proceder con confianza con el build de PyInstaller"
}

# Ejecutar función principal
main "$@"
