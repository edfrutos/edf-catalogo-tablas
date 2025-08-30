#!/bin/bash

# Script para configurar CI/CD con directorios requeridos
# Autor: EDF Developer - 2025

set -e

echo "🔧 CONFIGURACIÓN DE CI/CD PARA EDF CATÁLOGO DE TABLAS"
echo "=================================================="

# Función para crear directorios requeridos
create_required_directories() {
    echo "📁 Creando directorios requeridos..."
    
    # Lista de directorios que pueden ser referenciados en .spec files
    directories=(
        "backups"
        "backup_empty_files"
        "uploads"
        "static"
        "flask_session"
        "instance"
        "spreadsheets"
        "exportados"
        "imagenes"
        "logs"
        "app_data"
        "docs"
        "tools/build"
        "tools/db_utils"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo "   ✅ Creado: $dir"
        else
            echo "   ⚠️  Ya existe: $dir"
        fi
    done
    
    echo "✅ Directorios requeridos creados"
}

# Función para verificar archivos críticos
verify_critical_files() {
    echo "🔍 Verificando archivos críticos..."
    
    critical_files=(
        "EDF_CatalogoDeTablas_Native_Finder.spec"
        "launcher_native_websockets_fixed.py"
        ".env"
        "requirements.txt"
        "app/__init__.py"
    )
    
    missing_files=()
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ Existe: $file"
        else
            echo "   ❌ Faltante: $file"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "✅ Todos los archivos críticos están presentes"
        return 0
    else
        echo "❌ Faltan archivos críticos: ${missing_files[*]}"
        return 1
    fi
}

# Función para corregir archivo .spec problemático
fix_problematic_spec() {
    echo "🔧 Corrigiendo archivo .spec problemático..."
    
    spec_file="EDF_CatalogoDeTablas_Native_WebSockets.spec"
    
    if [ ! -f "$spec_file" ]; then
        echo "   ⚠️  Archivo $spec_file no encontrado"
        return 0
    fi
    
    # Crear backup
    cp "$spec_file" "${spec_file}.backup"
    echo "   📋 Backup creado: ${spec_file}.backup"
    
    # Comentar líneas problemáticas
    sed -i.bak 's/^[[:space:]]*('\''backups'\'', '\''backups'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''backup_empty_files'\'', '\''backup_empty_files'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''uploads'\'', '\''uploads'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''static'\'', '\''static'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''flask_session'\'', '\''flask_session'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''instance'\'', '\''instance'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''spreadsheets'\'', '\''spreadsheets'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''exportados'\'', '\''exportados'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''imagenes'\'', '\''imagenes'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    sed -i.bak 's/^[[:space:]]*('\''logs'\'', '\''logs'\'')/# &  # Comentado para CI\/CD/' "$spec_file"
    
    echo "   ✅ Archivo $spec_file corregido para CI/CD"
}

# Función para mostrar información del sistema
show_system_info() {
    echo "📊 Información del sistema:"
    echo "   Sistema operativo: $(uname -s)"
    echo "   Arquitectura: $(uname -m)"
    echo "   Python: $(python3 --version 2>/dev/null || echo 'No disponible')"
    echo "   Directorio actual: $(pwd)"
    echo "   Espacio disponible: $(df -h . | tail -1 | awk '{print $4}')"
}

# Función principal
main() {
    echo "🚀 Iniciando configuración de CI/CD..."
    
    # Mostrar información del sistema
    show_system_info
    
    # Crear directorios requeridos
    create_required_directories
    
    # Verificar archivos críticos
    if ! verify_critical_files; then
        echo "❌ Error: Faltan archivos críticos"
        exit 1
    fi
    
    # Corregir archivo .spec problemático
    fix_problematic_spec
    
    echo ""
    echo "🎉 CONFIGURACIÓN DE CI/CD COMPLETADA"
    echo "=================================="
    echo "✅ Directorios requeridos creados"
    echo "✅ Archivos críticos verificados"
    echo "✅ Archivo .spec corregido"
    echo ""
    echo "📋 Próximos pasos:"
    echo "   1. Ejecutar: ./build_native_finder.sh"
    echo "   2. Verificar la aplicación construida"
    echo "   3. Probar funcionalidades"
}

# Ejecutar función principal
main "$@"
