#!/bin/bash

# Script de lanzamiento para la Interfaz Web Unificada de Scripts
# EDF CatalogoDeTablas - Combina spell check y build scripts

set -e

echo "🚀 Iniciando Interfaz Web Unificada de Scripts..."
echo "📁 Directorio actual: $(pwd)"
echo "🔧 Verificando dependencias..."

# Verificar que estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que existe la interfaz web unificada
if [ ! -f "tools/unified_web_interface.py" ]; then
    echo "❌ Error: No se encuentra tools/unified_web_interface.py"
    exit 1
fi

# Verificar que existe el gestor unificado
if [ ! -f "tools/unified_scripts_manager.py" ]; then
    echo "❌ Error: No se encuentra tools/unified_scripts_manager.py"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."

# Verificar Flask
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask no está instalado. Instalando..."
    pip install flask
fi

# Verificar toml
if ! python -c "import toml" 2>/dev/null; then
    echo "⚠️  Instalando toml..."
    pip install toml
fi

# Verificar que existen las plantillas
if [ ! -d "tools/templates" ]; then
    echo "❌ Error: No se encuentra el directorio tools/templates"
    echo "💡 Creando directorio de plantillas..."
    mkdir -p tools/templates
fi

echo "✅ Dependencias verificadas"
echo "🔧 Verificando gestor de scripts..."

# Probar el gestor de scripts
if python -c "from tools.unified_scripts_manager import UnifiedScriptsManager; manager = UnifiedScriptsManager(); print('✅ Gestor funcionando')" 2>/dev/null; then
    echo "✅ Gestor de scripts funcionando correctamente"
else
    echo "❌ Error: El gestor de scripts no funciona correctamente"
    exit 1
fi

echo ""
echo "🌐 Iniciando servidor web..."
echo "📋 Información del servidor:"
echo "   - URL: http://localhost:5003"
echo "   - Puerto: 5003"
echo "   - Modo: Desarrollo"
echo ""
echo "🔧 FUNCIONALIDADES DISPONIBLES:"
echo "   📁 Scripts - Gestión de todos los scripts por categorías"
echo "   🔍 Spell Check - Dashboard específico para verificación ortográfica"
echo "   🚀 CI/CD - Scripts críticos para GitHub Actions"
echo "   📚 Documentation - Scripts referenciados en documentación"
echo "   🔧 Utilities - Scripts de utilidades generales"
echo "   ⚙️ Configuration - Scripts de configuración y verificación"
echo ""
echo "💡 Para detener el servidor, presiona Ctrl+C"
echo ""

# Iniciar la interfaz web
cd "$(dirname "$0")"
python unified_web_interface.py
