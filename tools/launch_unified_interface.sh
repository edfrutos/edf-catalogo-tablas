#!/bin/bash

# Script de lanzamiento para la Interfaz Unificada de Scripts
# EDF CatalogoDeTablas - Combina spell check y build scripts

set -e

echo "🚀 Iniciando Interfaz Unificada de Scripts..."
echo "📁 Directorio actual: $(pwd)"
echo "🔧 Verificando dependencias..."

# Verificar que estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
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

# Verificar tkinter
python -c "import tkinter" 2>/dev/null || {
    echo "❌ Error: tkinter no está disponible"
    echo "💡 En macOS, instala Python con tkinter: brew install python-tk"
    exit 1
}

# Verificar toml
python -c "import toml" 2>/dev/null || {
    echo "⚠️  Instalando toml..."
    pip install toml
}

# Verificar que existen los scripts de spell check
spell_check_scripts=(
    "quick_spell_check.py"
    "quick_setup_spell_check.py"
    "complete_spell_check_workflow.py"
    "add_common_words.py"
    "add_categorized_words.py"
    "fix_spell_check.py"
)

echo "🔍 Verificando scripts de spell check..."
for script in "${spell_check_scripts[@]}"; do
    if [ -f "tools/$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ⚠️  $script (no encontrado)"
    fi
done

# Verificar scripts de build
build_scripts=(
    "build_macos_app.sh"
    "verify_build_environment.sh"
    "verify_requirements.sh"
    "build_web_app.sh"
    "build_native_app.sh"
    "build_all_versions.sh"
)

echo "🔧 Verificando scripts de build..."
for script in "${build_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ⚠️  $script (no encontrado)"
    fi
done

echo ""
echo "✅ Dependencias verificadas"
echo "🎨 Iniciando interfaz gráfica..."
echo ""
echo "🔧 FUNCIONALIDADES DISPONIBLES:"
echo "   📁 Scripts - Gestión de todos los scripts por categorías"
echo "   🔍 Spell Check - Verificación ortográfica y corrección"
echo "   📋 Logs - Registro de actividades y resultados"
echo ""
echo "💡 Para cerrar la interfaz, cierra la ventana"
echo ""

# Lanzar la interfaz
python tools/unified_scripts_manager.py

echo "✅ Interfaz cerrada"
