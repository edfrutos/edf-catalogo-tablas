#!/bin/bash

# Script de lanzamiento para la interfaz gráfica de spell check
# Autor: EDF Developer - 2025

echo "🚀 Lanzando interfaz gráfica de Spell Check..."

# Verificar que estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que existe el script de la interfaz
if [ ! -f "tools/spell_check_gui.py" ]; then
    echo "❌ Error: No se encuentra tools/spell_check_gui.py"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."
python -c "import tkinter" 2>/dev/null || {
    echo "❌ Error: tkinter no está disponible"
    echo "💡 En macOS, instala Python con tkinter: brew install python-tk"
    exit 1
}

python -c "import toml" 2>/dev/null || {
    echo "⚠️  Instalando toml..."
    pip install toml
}

# Lanzar la interfaz
echo "🎨 Iniciando interfaz gráfica..."
python tools/spell_check_gui.py

echo "✅ Interfaz cerrada"
