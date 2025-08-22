#!/bin/bash

# Script de lanzamiento para la Interfaz Web de Gestión de Scripts de Build
# EDF CatalogoDeTablas

set -e

echo "🚀 Iniciando Interfaz Web de Gestión de Scripts de Build..."
echo "📁 Directorio actual: $(pwd)"
echo "🔧 Verificando dependencias..."

# Verificar que estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que existe el gestor de scripts
if [ ! -f "tools/build_scripts_manager.py" ]; then
    echo "❌ Error: No se encuentra tools/build_scripts_manager.py"
    exit 1
fi

# Verificar que existe la interfaz web
if [ ! -f "tools/build_interface.py" ]; then
    echo "❌ Error: No se encuentra tools/build_interface.py"
    exit 1
fi

# Verificar que existen las plantillas
if [ ! -d "tools/templates" ]; then
    echo "❌ Error: No se encuentra el directorio tools/templates"
    exit 1
fi

# Verificar que Flask está instalado
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask no está instalado. Instalando..."
    pip install flask
fi

echo "✅ Dependencias verificadas"
echo "🔧 Verificando gestor de scripts..."

# Probar el gestor de scripts
if python tools/build_scripts_manager.py list > /dev/null 2>&1; then
    echo "✅ Gestor de scripts funcionando correctamente"
else
    echo "❌ Error: El gestor de scripts no funciona correctamente"
    exit 1
fi

echo ""
echo "🌐 Iniciando servidor web..."
echo "📋 Información del servidor:"
echo "   - URL: http://localhost:5002"
echo "   - Puerto: 5002"
echo "   - Modo: Desarrollo"
echo ""
echo "🔧 Funcionalidades disponibles:"
echo "   - Vista general de categorías"
echo "   - Detalle de scripts por categoría"
echo "   - Ejecución de scripts desde la web"
echo "   - API REST para integración"
echo "   - Verificación de salud del sistema"
echo ""
echo "💡 Para detener el servidor, presiona Ctrl+C"
echo ""

# Iniciar la interfaz web
cd "$(dirname "$0")"
python build_interface.py
