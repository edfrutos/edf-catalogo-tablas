#!/bin/bash

# ==============================================
# 🚀 SCRIPT: Iniciar App en Puerto 5001
# ==============================================

APP_NAME="EDF_CatalogoDeTablas"
PORT=5001
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Iniciando $APP_NAME en puerto $PORT"
echo "=================================================="

# Cambiar al directorio del proyecto
cd "$PROJECT_ROOT" || {
    echo "❌ Error: No se pudo cambiar al directorio del proyecto"
    exit 1
}

echo "📁 Directorio del proyecto: $(pwd)"

# Verificar que estamos en el entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  No se detectó entorno virtual activo"
    echo "💡 Activando entorno virtual..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "✅ Entorno virtual activado"
    else
        echo "❌ Error: No se encontró el entorno virtual en .venv/"
        exit 1
    fi
else
    echo "✅ Entorno virtual activo: $VIRTUAL_ENV"
fi

# Verificar que Flask esté instalado
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Error: Flask no está instalado"
    echo "💡 Instalando dependencias..."
    pip install -r requirements_python310.txt
fi

# Ejecutar script de verificación de puerto
echo "🔍 Verificando puerto $PORT..."
if ! "$SCRIPT_DIR/check_and_free_port_5001.sh"; then
    echo "❌ Error: No se pudo verificar/liberar el puerto $PORT"
    exit 1
fi

# Configurar variables de entorno para desarrollo
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=wsgi.py

echo "⚙️  Configuración de entorno:"
echo "   - FLASK_ENV: $FLASK_ENV"
echo "   - FLASK_DEBUG: $FLASK_DEBUG"
echo "   - FLASK_APP: $FLASK_APP"
echo "   - Puerto: $PORT"

# Verificar que el archivo wsgi.py existe
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: No se encontró wsgi.py"
    exit 1
fi

echo "=================================================="
echo "🎯 Iniciando $APP_NAME..."
echo "🌐 URL: http://localhost:$PORT"
echo "🔧 Debug: Habilitado"
echo "🔄 Hot reload: Habilitado"
echo "=================================================="

# Iniciar la aplicación
exec flask run --debug --port=$PORT --host=0.0.0.0
