#!/bin/bash

# Script para verificar y crear requirements_python310.txt
# Soluciona el problema del workflow de GitHub Actions

echo "📦 VERIFICACIÓN DE REQUIREMENTS"
echo "==============================="

REQUIREMENTS_FILE="requirements_python310.txt"
BACKUP_FILE="requirements.txt"

echo "🔍 Verificando archivo $REQUIREMENTS_FILE..."

# Verificar si el archivo existe
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "✅ $REQUIREMENTS_FILE existe"
    echo "📏 Tamaño: $(wc -l < "$REQUIREMENTS_FILE") líneas"
    echo "📋 Primeras 5 líneas:"
    head -5 "$REQUIREMENTS_FILE"
    exit 0
fi

echo "❌ $REQUIREMENTS_FILE no encontrado"
echo "🔧 Intentando crear el archivo..."

# Verificar si existe requirements.txt como backup
if [ -f "$BACKUP_FILE" ]; then
    echo "📋 Copiando $BACKUP_FILE a $REQUIREMENTS_FILE..."
    cp "$BACKUP_FILE" "$REQUIREMENTS_FILE"
    echo "✅ Archivo creado desde $BACKUP_FILE"
    echo "📏 Tamaño: $(wc -l < "$REQUIREMENTS_FILE") líneas"
    exit 0
fi

echo "❌ $BACKUP_FILE tampoco existe"
echo "🔧 Creando archivo $REQUIREMENTS_FILE básico..."

# Crear archivo requirements básico
cat > "$REQUIREMENTS_FILE" << 'EOF'
# Requirements para Python 3.10 - EDF Catálogo de Tablas
# Flask y dependencias web
Flask==2.3.3
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7

# Base de datos
pymongo==4.5.0

# AWS
boto3==1.28.44
botocore==1.31.44

# Procesamiento de datos
pandas==2.0.3
openpyxl==3.1.2
xlrd==2.0.1

# Utilidades
python-dotenv==1.0.0
requests==2.31.0
urllib3==2.0.4

# Seguridad
cryptography==41.0.4
PyJWT==2.8.0

# Imágenes
Pillow==10.0.1

# Desarrollo
pytest==7.4.2
black==23.7.0
flake8==6.0.0
ruff==0.0.284

# Sistema
psutil==5.9.5
pywebview==4.4.1
EOF

echo "✅ Archivo $REQUIREMENTS_FILE creado con dependencias básicas"
echo "📏 Tamaño: $(wc -l < "$REQUIREMENTS_FILE") líneas"
echo "📋 Primeras 10 líneas:"
head -10 "$REQUIREMENTS_FILE"

echo ""
echo "📊 RESUMEN"
echo "=========="
echo "✅ Archivo $REQUIREMENTS_FILE creado/verificado"
echo "📋 Dependencias incluidas: Flask, MongoDB, AWS, pandas, etc."
echo "🎯 Listo para el workflow de GitHub Actions"
