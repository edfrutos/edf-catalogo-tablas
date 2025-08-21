#!/bin/bash

# Script de verificación final antes del build
# Se ejecuta justo antes de PyInstaller para asegurar que no hay conflictos
# Autor: EDF Developer - 2025

set -e

echo "🔍 VERIFICACIÓN FINAL PRE-BUILD..."

# Función para verificación final del archivo .spec
check_spec_file() {
    echo "📄 Verificando archivo .spec..."
    
    if [ ! -f "EDF_CatalogoDeTablas.spec" ]; then
        echo "❌ Error: No se encuentra EDF_CatalogoDeTablas.spec"
        return 1
    fi
    
    # Verificar que no hay referencias problemáticas
    if grep -q "app_tools" EDF_CatalogoDeTablas.spec; then
        echo "❌ Error: El archivo .spec aún contiene referencias a 'app_tools'"
        echo "🔧 Aplicando corrección automática..."
        sed -i '' 's/app_tools/app_utils/g' EDF_CatalogoDeTablas.spec
        echo "✅ Corrección aplicada"
    else
        echo "✅ No hay referencias problemáticas a 'app_tools'"
    fi
    
    # Verificar que se usan referencias seguras
    if grep -q "app_utils" EDF_CatalogoDeTablas.spec; then
        echo "✅ Se usan referencias seguras a 'app_utils'"
    else
        echo "❌ Error: No se encontraron referencias a 'app_utils'"
        return 1
    fi
    
    echo "✅ Archivo .spec verificado correctamente"
    return 0
}

# Función para verificar que no hay archivos conflictivos
check_conflict_files() {
    echo "🔍 Verificando archivos conflictivos..."
    
    # Verificar que no hay archivos llamados 'tools'
    if [ -f "tools" ]; then
        echo "❌ Error: Existe un archivo 'tools' conflictivo"
        rm -f tools
        echo "✅ Archivo conflictivo eliminado"
    else
        echo "✅ No hay archivo 'tools' conflictivo"
    fi
    
    # Buscar archivos conflictivos en el proyecto
    if find . -name "tools" -type f 2>/dev/null | grep -q .; then
        echo "❌ Error: Existen archivos 'tools' conflictivos en el proyecto"
        find . -name "tools" -type f -delete 2>/dev/null || true
        echo "✅ Archivos conflictivos eliminados"
    else
        echo "✅ No hay archivos 'tools' conflictivos"
    fi
    
    # Verificar que el directorio tools existe
    if [ ! -d "tools" ]; then
        echo "❌ Error: El directorio 'tools' no existe"
        return 1
    else
        echo "✅ Directorio 'tools' existe correctamente"
    fi
    
    echo "✅ Verificación de archivos conflictivos completada"
    return 0
}

# Función para verificar el entorno de PyInstaller
check_pyinstaller_environment() {
    echo "🔍 Verificando entorno de PyInstaller..."
    
    # Verificar que PyInstaller está instalado
    if ! command -v pyinstaller &> /dev/null; then
        echo "❌ Error: PyInstaller no está instalado"
        return 1
    else
        echo "✅ PyInstaller está instalado"
    fi
    
    # Verificar que el archivo principal existe
    if [ ! -f "run_server.py" ]; then
        echo "❌ Error: No se encuentra run_server.py"
        return 1
    else
        echo "✅ run_server.py existe"
    fi
    
    # Limpiar caché de PyInstaller
    echo "🧹 Limpiando caché de PyInstaller..."
    pyinstaller --clean 2>/dev/null || true
    
    echo "✅ Entorno de PyInstaller verificado"
    return 0
}

# Función para mostrar resumen final
show_final_summary() {
    echo ""
    echo "📋 RESUMEN FINAL PRE-BUILD:"
    echo "   - Archivo .spec: ✅ VERIFICADO"
    echo "   - Archivos conflictivos: ✅ VERIFICADO"
    echo "   - Entorno PyInstaller: ✅ VERIFICADO"
    echo "   - Directorio tools: ✅ VERIFICADO"
    echo ""
    echo "🎉 VERIFICACIÓN FINAL COMPLETADA"
    echo "💡 El entorno está listo para el build"
    echo "🚀 Puedes ejecutar PyInstaller con confianza"
}

# Función principal
main() {
    echo "🚀 Ejecutando verificación final pre-build..."
    
    if check_spec_file && check_conflict_files && check_pyinstaller_environment; then
        show_final_summary
        echo "✅ Verificación final exitosa"
    else
        echo "❌ Error: La verificación final falló"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
