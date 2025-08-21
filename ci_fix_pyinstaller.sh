#!/bin/bash

# Script específico para entornos de CI/CD que resuelve conflictos de PyInstaller
# Autor: EDF Developer - 2025
# Uso: ./ci_fix_pyinstaller.sh

set -e  # Salir si hay algún error

echo "🔧 CI/CD: Resolviendo conflictos de PyInstaller..."

# Función para limpiar conflictos específicos
clean_pyinstaller_conflicts() {
    echo "🧹 Limpiando conflictos de PyInstaller..."
    
    # Eliminar directorios de build
    rm -rf build/ dist/ __pycache__/ .pytest_cache/
    
    # Eliminar archivos .spec
    rm -f *.spec
    
    # Eliminar archivos Python compilados
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    find . -name "*.pyd" -delete 2>/dev/null || true
    
    # Eliminar directorios __pycache__
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Eliminar archivos temporales
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "*.swp" -delete 2>/dev/null || true
    find . -name "*.swo" -delete 2>/dev/null || true
    
    # LIMPIEZA ESPECÍFICA PARA EL CONFLICTO DE TOOLS
    echo "🔍 Limpieza específica para conflicto de directorio 'tools'..."
    
    # Verificar y eliminar archivos conflictivos específicos
    if [ -f "tools" ]; then
        echo "⚠️  Eliminando archivo conflictivo 'tools'"
        rm -f tools
    fi
    
    # Verificar en directorios de PyInstaller
    if [ -d "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks" ]; then
        if [ -f "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks/tools" ]; then
            echo "⚠️  Eliminando archivo conflictivo en Frameworks"
            rm -f "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks/tools"
        fi
    fi
    
    # Verificar en directorio dist completo
    if [ -d "dist" ]; then
        echo "🔍 Buscando archivos conflictivos en dist..."
        find dist/ -name "tools" -type f -delete 2>/dev/null || true
        find dist/ -name "tools" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Verificar en directorio build completo
    if [ -d "build" ]; then
        echo "🔍 Buscando archivos conflictivos en build..."
        find build/ -name "tools" -type f -delete 2>/dev/null || true
        find build/ -name "tools" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Limpiar caché de PyInstaller
    echo "🧹 Limpiando caché de PyInstaller..."
    if command -v pyinstaller &> /dev/null; then
        pyinstaller --clean 2>/dev/null || true
    fi
    
    # Verificar que el directorio tools existe y es un directorio
    if [ ! -d "tools" ]; then
        echo "❌ Error: El directorio 'tools' no existe o no es un directorio"
        exit 1
    fi
    
    # Verificar que no hay archivos llamados 'tools' en el directorio raíz
    if [ -f "tools" ]; then
        echo "❌ Error: Existe un archivo llamado 'tools' que debe ser eliminado"
        rm -f tools
    fi
    
    echo "✅ Limpieza completada"
}

# Función para verificar el entorno
check_environment() {
    echo "🔍 Verificando entorno..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "config.py" ]; then
        echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
        exit 1
    fi
    
    # Verificar que existe el directorio tools
    if [ ! -d "tools" ]; then
        echo "❌ Error: No se encuentra el directorio tools."
        exit 1
    fi
    
    # Verificar que tools es un directorio, no un archivo
    if [ -f "tools" ]; then
        echo "❌ Error: 'tools' es un archivo, debe ser un directorio."
        exit 1
    fi
    
    echo "✅ Entorno verificado correctamente"
}

# Función para preparar el build
prepare_build() {
    echo "📦 Preparando build..."
    
    # Activar entorno virtual si existe
    if [ -d ".venv" ]; then
        echo "🔧 Activando entorno virtual..."
        source .venv/bin/activate
    fi
    
    # Verificar que PyInstaller está instalado
    if ! command -v pyinstaller &> /dev/null; then
        echo "❌ Error: PyInstaller no está instalado."
        echo "💡 Instala con: pip install pyinstaller"
        exit 1
    fi
    
    echo "✅ Build preparado"
}

# Función para verificar el estado final
verify_clean_state() {
    echo "🔍 Verificando estado final..."
    
    # Verificar que no hay archivos conflictivos
    if [ -f "tools" ]; then
        echo "❌ Error: Aún existe un archivo 'tools' conflictivo"
        return 1
    fi
    
    if [ -d "dist" ]; then
        if find dist/ -name "tools" -type f 2>/dev/null | grep -q .; then
            echo "❌ Error: Aún existen archivos 'tools' conflictivos en dist/"
            return 1
        fi
    fi
    
    if [ -d "build" ]; then
        if find build/ -name "tools" -type f 2>/dev/null | grep -q .; then
            echo "❌ Error: Aún existen archivos 'tools' conflictivos en build/"
            return 1
        fi
    fi
    
    echo "✅ Estado verificado correctamente"
    return 0
}

# Función principal
main() {
    echo "🚀 Iniciando resolución de conflictos para CI/CD..."
    
    check_environment
    clean_pyinstaller_conflicts
    prepare_build
    
    # Verificar estado final
    if ! verify_clean_state; then
        echo "❌ Error: No se pudieron resolver todos los conflictos"
        exit 1
    fi
    
    echo ""
    echo "📋 Estado final:"
    echo "   - Directorio actual: $(pwd)"
    echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
    echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio tools: $([ -d "tools" ] && echo "EXISTE (DIRECTORIO)" || echo "NO EXISTE")"
    echo "   - Archivo tools: $([ -f "tools" ] && echo "EXISTE (ARCHIVO - PROBLEMA)" || echo "NO EXISTE")"
    echo "   - PyInstaller: $(command -v pyinstaller &> /dev/null && echo "INSTALADO" || echo "NO INSTALADO")"
    
    echo ""
    echo "✅ Conflictos resueltos. Ahora puedes ejecutar el build sin problemas."
    echo "💡 Comando recomendado: ./build_macos_app.sh"
}

# Ejecutar función principal
main "$@"
