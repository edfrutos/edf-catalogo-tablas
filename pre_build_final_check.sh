#!/bin/bash

echo "🔍 Verificación final pre-build..."

# Crear directorios esenciales si no existen
echo "📁 Creando directorios esenciales..."
mkdir -p app/static
mkdir -p app/templates
mkdir -p app/routes
mkdir -p app/models
mkdir -p app/utils
mkdir -p tools/db_utils
mkdir -p tools/utils
mkdir -p tools/maintenance
mkdir -p tools/monitoring
mkdir -p "tools/Admin Utils"
mkdir -p "tools/Scripts Principales"
mkdir -p "tools/Users Tools"
mkdir -p "tools/Test Scripts"
mkdir -p tools/testing
mkdir -p tools/image_utils
mkdir -p tools/local
mkdir -p tools/macOS
mkdir -p tools/production
mkdir -p tools/system
mkdir -p tools/src

# Crear directorios opcionales si no existen
echo "📁 Creando directorios opcionales..."
mkdir -p scripts
mkdir -p docs
mkdir -p static
mkdir -p spreadsheets
mkdir -p exportados
mkdir -p imagenes

# Verificar archivos esenciales
echo "📄 Verificando archivos esenciales..."
if [ ! -f ".env" ]; then
    echo "⚠️  Creando .env de ejemplo..."
    cat > .env << EOF
FLASK_ENV=production
APP_VERSION=1.0.0
BUILD_DATE=$(date +%Y-%m-%d)
EOF
fi

if [ ! -f "config.py" ]; then
    echo "⚠️  Creando config.py de ejemplo..."
    cat > config.py << EOF
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    DEBUG = False
EOF
fi

if [ ! -f "wsgi.py" ]; then
    echo "⚠️  Creando wsgi.py de ejemplo..."
    cat > wsgi.py << EOF
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
EOF
fi

# Verificar que el archivo .spec existe y es válido
echo "🔧 Verificando archivo .spec..."
if [ ! -f "EDF_CatalogoDeTablas_Native_WebSockets.spec" ]; then
    echo "❌ ERROR: EDF_CatalogoDeTablas_Native_WebSockets.spec no encontrado"
    exit 1
fi

echo "✅ Verificación final completada"
echo "📋 Directorios creados/verificados:"
ls -la | grep "^d"
echo "📋 Archivos esenciales verificados:"
ls -la .env config.py wsgi.py requirements_python310.txt 2>/dev/null || echo "Algunos archivos no encontrados"
