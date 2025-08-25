#!/bin/bash

# Script para construir la aplicación nativa con WebSockets
# EDF Catálogo de Tablas - Aplicación Nativa WebSockets

set -e

echo "🚀 Iniciando construcción de aplicación nativa con WebSockets..."
echo "=" * 60

# Verificar entorno
if [ ! -d ".venv" ]; then
    echo "❌ Error: Entorno virtual no encontrado"
    echo "Ejecuta: python3 -m venv .venv && source .venv/bin/activate"
    exit 1
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate

# Verificar dependencias
echo "📦 Verificando dependencias..."
pip install -q websockets

# Verificar archivos necesarios
echo "🔍 Verificando archivos necesarios..."
required_files=(
    "launcher_native_websockets.py"
    "EDF_CatalogoDeTablas_Native_WebSockets.spec"
    "wsgi.py"
    "config.py"
    ".env"
    "app/static/favicon.icns"
    "app/static/favicon.ico"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Archivo no encontrado: $file"
        exit 1
    fi
done

echo "✅ Todos los archivos necesarios encontrados"

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf dist/ build/ __pycache__/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p dist/
mkdir -p build/

# Construir aplicación con PyInstaller
echo "🔨 Construyendo aplicación con PyInstaller..."
python -m PyInstaller EDF_CatalogoDeTablas_Native_WebSockets.spec

# Verificar que se creó la aplicación
if [ ! -d "dist/EDF_CatalogoDeTablas_Web_Native.app" ]; then
    echo "❌ Error: No se pudo crear la aplicación .app"
    exit 1
fi

echo "✅ Aplicación construida exitosamente"
echo "📱 Aplicación ubicada en: dist/EDF_CatalogoDeTablas_Web_Native.app"
echo "🎨 Icono incluido: app/static/favicon.icns"

# Crear DMG
echo "💿 Creando DMG..."
./create_dmg_websockets.sh

echo ""
echo "🎉 ¡Construcción completada!"
echo "📱 Aplicación: dist/EDF_CatalogoDeTablas_WebSockets.app"
echo "💿 DMG: dist/EDF_CatalogoDeTablas_WebSockets.dmg"
echo ""
echo "🚀 Para ejecutar la aplicación:"
echo "   open dist/EDF_CatalogoDeTablas_WebSockets.app"
echo ""
echo "📋 Características de la aplicación:"
echo "   • Aplicación nativa de macOS"
echo "   • Interfaz web completa en ventana nativa"
echo "   • Comunicación WebSockets en tiempo real"
echo "   • Sin dependencia de navegador externo"
echo "   • Misma funcionalidad que la aplicación web"
echo "   • Gestión de catálogos, usuarios y herramientas"
