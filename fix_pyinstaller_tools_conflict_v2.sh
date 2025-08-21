#!/bin/bash

# Script específico para resolver el conflicto de PyInstaller con el directorio tools
# Versión 2.0 - Enfoque más agresivo y específico
# Autor: EDF Developer - 2025

set -e

echo "🔧 FIX V2: Resolviendo conflicto específico de PyInstaller con directorio 'tools'..."

# Función para limpieza completa y específica
aggressive_tools_cleanup() {
    echo "🧹 Limpieza agresiva y específica para conflicto de 'tools'..."
    
    # 1. Limpiar directorios de build completamente
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
    
    # 5. LIMPIEZA ESPECÍFICA PARA CONFLICTO DE TOOLS
    echo "🔧 Limpieza específica para conflicto de directorio 'tools'..."
    
    # Verificar y eliminar archivos conflictivos específicos
    if [ -f "tools" ]; then
        echo "⚠️  Eliminando archivo conflictivo 'tools' en directorio raíz"
        rm -f tools
    fi
    
    # Buscar y eliminar TODOS los archivos llamados 'tools' en el proyecto
    echo "🔍 Buscando y eliminando TODOS los archivos 'tools' conflictivos..."
    find . -name "tools" -type f -delete 2>/dev/null || true
    
    # Buscar y eliminar archivos 'tools' en directorios específicos de PyInstaller
    echo "🔍 Limpiando archivos 'tools' en directorios de PyInstaller..."
    if [ -d "dist" ]; then
        find dist/ -name "tools" -type f -delete 2>/dev/null || true
        find dist/ -name "tools" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    if [ -d "build" ]; then
        find build/ -name "tools" -type f -delete 2>/dev/null || true
        find build/ -name "tools" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # 6. Limpiar caché de PyInstaller de manera más agresiva
    echo "🧹 Limpiando caché de PyInstaller de manera agresiva..."
    if command -v pyinstaller &> /dev/null; then
        pyinstaller --clean 2>/dev/null || true
        pyinstaller --distpath /tmp/pyinstaller_cleanup --workpath /tmp/pyinstaller_cleanup --clean 2>/dev/null || true
    fi
    
    # 7. Verificar que el directorio tools existe y es un directorio
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

# Función para verificar estado final
verify_final_state() {
    echo "🔍 Verificando estado final..."
    
    # Verificar que no hay archivos conflictivos
    if [ -f "tools" ]; then
        echo "❌ Error: Aún existe un archivo 'tools' conflictivo en el directorio raíz"
        return 1
    fi
    
    # Verificar que no hay archivos 'tools' en todo el proyecto
    if find . -name "tools" -type f 2>/dev/null | grep -q .; then
        echo "❌ Error: Aún existen archivos 'tools' conflictivos en el proyecto:"
        find . -name "tools" -type f 2>/dev/null
        return 1
    fi
    
    # Verificar que el directorio tools existe
    if [ ! -d "tools" ]; then
        echo "❌ Error: El directorio 'tools' no existe después de la limpieza"
        return 1
    fi
    
    echo "✅ Estado final verificado correctamente"
    return 0
}

# Función para mostrar estado detallado
show_detailed_state() {
    echo ""
    echo "📋 ESTADO DETALLADO DESPUÉS DE LA LIMPIEZA:"
    echo "   - Directorio actual: $(pwd)"
    echo "   - Archivos .spec: $(ls -la *.spec 2>/dev/null | wc -l | tr -d ' ')"
    echo "   - Directorio dist: $([ -d "dist" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio build: $([ -d "build" ] && echo "EXISTE" || echo "NO EXISTE")"
    echo "   - Directorio tools: $([ -d "tools" ] && echo "EXISTE (DIRECTORIO)" || echo "NO EXISTE")"
    echo "   - Archivo tools: $([ -f "tools" ] && echo "EXISTE (ARCHIVO - PROBLEMA)" || echo "NO EXISTE")"
    echo "   - PyInstaller: $(command -v pyinstaller &> /dev/null && echo "INSTALADO" || echo "NO INSTALADO")"
    
    # Verificar archivos 'tools' conflictivos
    echo "   - Archivos 'tools' conflictivos: $(find . -name "tools" -type f 2>/dev/null | wc -l | tr -d ' ')"
    
    echo ""
}

# Función principal
main() {
    echo "🚀 Iniciando resolución de conflictos V2 para PyInstaller..."
    
    verify_environment
    aggressive_tools_cleanup
    show_detailed_state
    
    # Verificar estado final
    if ! verify_final_state; then
        echo "❌ Error: No se pudieron resolver todos los conflictos"
        exit 1
    fi
    
    echo ""
    echo "✅ Conflictos resueltos exitosamente con V2."
    echo "💡 Ahora puedes ejecutar el build sin problemas."
    echo "🚀 Comando recomendado: ./build_macos_app.sh"
}

# Ejecutar función principal
main "$@"
