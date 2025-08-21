#!/bin/bash

# Script de limpieza pre-build para CI/CD
# Se ejecuta justo antes del build para asegurar un entorno limpio
# Autor: EDF Developer - 2025

set -e

echo "🧹 PRE-BUILD: Limpieza agresiva para CI/CD..."

# Función para limpieza completa
aggressive_cleanup() {
    echo "🔍 Limpieza agresiva iniciada..."
    
    # 1. Limpiar directorios de build
    echo "📁 Limpiando directorios de build..."
    rm -rf build/ dist/ __pycache__/ .pytest_cache/ .mypy_cache/
    
    # 2. Limpiar archivos .spec
    echo "📄 Limpiando archivos .spec..."
    rm -f *.spec
    
    # 3. Limpiar archivos Python compilados
    echo "🐍 Limpiando archivos Python compilados..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    find . -name "*.pyd" -delete 2>/dev/null || true
    
    # 4. Limpiar directorios __pycache__
    echo "📦 Limpiando directorios __pycache__..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 5. Limpiar archivos temporales
    echo "🗂️ Limpiando archivos temporales..."
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "*.swp" -delete 2>/dev/null || true
    find . -name "*.swo" -delete 2>/dev/null || true
    find . -name "*~" -delete 2>/dev/null || true
    
    # 6. LIMPIEZA ESPECÍFICA PARA CONFLICTO DE TOOLS
    echo "🔧 Limpieza específica para conflicto de directorio 'tools'..."
    
    # Verificar y eliminar archivos conflictivos específicos
    if [ -f "tools" ]; then
        echo "⚠️  Eliminando archivo conflictivo 'tools'"
        rm -f tools
    fi
    
    # Buscar y eliminar archivos 'tools' en todo el proyecto
    echo "🔍 Buscando archivos 'tools' conflictivos..."
    find . -name "tools" -type f -delete 2>/dev/null || true
    
    # 7. Limpiar caché de PyInstaller
    echo "🧹 Limpiando caché de PyInstaller..."
    if command -v pyinstaller &> /dev/null; then
        pyinstaller --clean 2>/dev/null || true
    fi
    
    # 8. Verificar estado del directorio tools
    echo "🔍 Verificando estado del directorio tools..."
    if [ ! -d "tools" ]; then
        echo "❌ Error: El directorio 'tools' no existe"
        exit 1
    fi
    
    if [ -f "tools" ]; then
        echo "❌ Error: Existe un archivo 'tools' que debe ser eliminado"
        rm -f tools
    fi
    
    echo "✅ Limpieza agresiva completada"
}

# Función para verificar el entorno
verify_environment() {
    echo "🔍 Verificando entorno..."
    
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
    
    echo "✅ Entorno verificado correctamente"
}

# Función para mostrar estado final
show_final_state() {
    echo ""
    echo "📋 Estado final después de la limpieza:"
    echo "   - Directorio actual: $(pwd)"
    echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
    echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio tools: $([ -d "tools" ] && echo "EXISTE (DIRECTORIO)" || echo "NO EXISTE")"
    echo "   - Archivo tools: $([ -f "tools" ] && echo "EXISTE (ARCHIVO - PROBLEMA)" || echo "NO EXISTE")"
    echo "   - PyInstaller: $(command -v pyinstaller &> /dev/null && echo "INSTALADO" || echo "NO INSTALADO")"
    
    # Verificar que no hay archivos conflictivos
    if [ -f "tools" ]; then
        echo "❌ ERROR: Aún existe un archivo 'tools' conflictivo"
        exit 1
    fi
    
    if find . -name "tools" -type f 2>/dev/null | grep -q .; then
        echo "❌ ERROR: Aún existen archivos 'tools' conflictivos en el proyecto"
        find . -name "tools" -type f 2>/dev/null
        exit 1
    fi
    
    echo "✅ Estado verificado correctamente"
}

# Función principal
main() {
    echo "🚀 Iniciando limpieza pre-build para CI/CD..."
    
    verify_environment
    aggressive_cleanup
    show_final_state
    
    echo ""
    echo "✅ Limpieza pre-build completada exitosamente"
    echo "💡 El entorno está listo para el build"
}

# Ejecutar función principal
main "$@"
