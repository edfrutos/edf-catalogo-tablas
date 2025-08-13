#!/bin/bash

# Script para construir la aplicación macOS EDF CatálogoDeTablas
# Uso: ./build_macos_app.sh

set -e  # Salir si hay algún error

echo "🍎 Iniciando construcción de aplicación macOS..."

# Verificar que estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: Este script debe ejecutarse en macOS"
    exit 1
fi

# Verificar Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Error: Python 3.10 no está instalado"
    echo "💡 Instala Python 3.10 con: brew install python@3.10"
    exit 1
fi

# Verificar PyInstaller
if ! python3.10 -c "import PyInstaller" &> /dev/null; then
    echo "📦 Instalando PyInstaller..."
    python3.10 -m pip install pyinstaller==6.15.0 pyinstaller-hooks-contrib==2025.8
fi

# Verificar PyWebView
if ! python3.10 -c "import webview" &> /dev/null; then
    echo "📦 Instalando PyWebView..."
    python3.10 -m pip install pywebview
fi

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf build/ dist/ __pycache__/ *.pyc

# Crear directorio de logs si no existe
mkdir -p logs

# Construir la aplicación
echo "🔨 Construyendo aplicación con PyInstaller..."
python3.10 -m PyInstaller EDF_CatalogoDeTablas.spec --clean

# Verificar que se creó la aplicación
if [ -d "dist/EDF_CatalogoDeTablas.app" ]; then
    echo "✅ Aplicación construida exitosamente!"
    echo "📁 Ubicación: dist/EDF_CatalogoDeTablas.app"
    echo "🚀 Para ejecutar: open dist/EDF_CatalogoDeTablas.app"
    
    # Mostrar información del bundle
    echo ""
    echo "📋 Información del bundle:"
    ls -la dist/EDF_CatalogoDeTablas.app/Contents/MacOS/
    
    # Verificar tamaño
    echo ""
    echo "📏 Tamaño de la aplicación:"
    du -sh dist/EDF_CatalogoDeTablas.app
    
else
    echo "❌ Error: No se pudo crear la aplicación"
    exit 1
fi

echo ""
echo "🎉 ¡Construcción completada!"
echo "💡 Para distribuir, comprime: dist/EDF_CatalogoDeTablas.app"
