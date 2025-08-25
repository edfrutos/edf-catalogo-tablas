#!/bin/bash

# Script para construir la aplicación macOS EDF_CatalogoDeTablas
# Autor: EDF Developer - 2025

set -e  # Salir si hay algún error

echo "🚀 Iniciando construcción de la aplicación macOS..."

# Verificar que estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: No se encuentra config.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Activar entorno virtual (si existe) o usar Python global
echo "📦 Verificando entorno virtual..."
if [ -f ".venv/bin/activate" ]; then
    echo "✅ Entorno virtual encontrado, activando..."
    source .venv/bin/activate
else
    echo "⚠️  Entorno virtual no encontrado, usando Python global..."
    echo "📋 Python disponible: $(which python)"
    echo "📋 Versión de Python: $(python --version)"
fi

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
./clean_build.sh

# Resolver conflictos específicos de PyInstaller
echo "🔧 Resolviendo conflictos específicos de PyInstaller..."
./fix_pyinstaller_tools_conflict.sh

# Verificar que existe el archivo .spec correcto
if [ -f "EDF_CatalogoDeTablas.spec" ]; then
    echo "✅ Archivo .spec existente encontrado, usando el existente..."
else
    echo "❌ Error: No se encuentra el archivo EDF_CatalogoDeTablas.spec"
    echo "🔧 Creando archivo .spec básico..."
    cat > EDF_CatalogoDeTablas.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/static', 'app/static'),
        ('app/templates', 'app/templates'),
        ('.env', '.'),
        ('config.py', '.'),
        ('wsgi.py', '.'),
        ('app/__init__.py', 'app'),
        ('app/routes', 'app/routes'),
        ('app/models', 'app/models'),
        ('app/utils', 'app/utils'),
        ('app/extensions.py', 'app'),
        ('app/logging_unified.py', 'app'),
        ('app/security_middleware.py', 'app'),
        ('scripts', 'scripts'),
        ('tools/db_utils', 'app_tools/db_utils'),
        ('tools/utils', 'app_tools/utils'),
        ('tools/maintenance', 'app_tools/maintenance'),
        ('tools/monitoring', 'app_tools/monitoring'),
        ('tools/Admin Utils', 'app_tools/Admin Utils'),
        ('tools/Scripts Principales', 'app_tools/Scripts Principales'),
        ('tools/Users Tools', 'app_tools/Users Tools'),
        ('tools/Test Scripts', 'app_tools/Test Scripts'),
        ('tools/testing', 'app_tools/testing'),
        ('tools/image_utils', 'app_tools/image_utils'),
        ('tools/local', 'app_tools/local'),
        ('tools/macOS', 'app_tools/macOS'),
        ('tools/production', 'app_tools/production'),
        ('tools/system', 'app_tools/system'),
        ('tools/src', 'app_tools/src'),
        ('docs', 'docs'),
        ('backups', 'backups'),
        ('backup_empty_files', 'backup_empty_files'),
        ('uploads', 'uploads'),
        ('static', 'static'),
        ('flask_session', 'flask_session'),
        ('instance', 'instance'),
        ('spreadsheets', 'spreadsheets'),
        ('exportados', 'exportados'),
        ('imagenes', 'imagenes'),
        ('app_data', 'app_data'),
        ('logs', 'logs'),
    ],
    hiddenimports=[
        'flask',
        'flask_login',
        'flask_session',
        'flask_mail',
        'flask_pymongo',
        'pymongo',
        'boto3',
        'botocore',
        'werkzeug',
        'jinja2',
        'dotenv',
        'requests',
        'bs4',
        'lxml',
        'openpyxl',
        'xlsxwriter',
        'reportlab',
        'PIL',
        'Pillow',
        'cryptography',
        'bcrypt',
        'email_validator',
        'pywebview',
        'app',
        'app.routes',
        'app.models',
        'app.utils',
        'app.extensions',
        'app.logging_unified',
        'app.security_middleware',
        'config',
        'wsgi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EDF_CatalogoDeTablas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDF_CatalogoDeTablas',
)
EOF
fi

# Verificar que no hay conflictos de directorios
echo "🔍 Verificando conflictos de directorios..."
if [ -d "dist" ]; then
    echo "🧹 Limpiando directorio dist completamente..."
    rm -rf dist/
fi

# Construir la aplicación
echo "🔨 Construyendo aplicación con PyInstaller..."
pyinstaller --clean EDF_CatalogoDeTablas.spec

# Verificar que la aplicación se construyó correctamente
if [ -d "dist/EDF_CatalogoDeTablas" ]; then
    echo "✅ Aplicación construida exitosamente en dist/EDF_CatalogoDeTablas/"
    
    # Mostrar información de la aplicación
    echo "📊 Información de la aplicación:"
    du -sh dist/EDF_CatalogoDeTablas/
    ls -la dist/EDF_CatalogoDeTablas/
    
    echo ""
    echo "🎉 ¡Construcción completada!"
    echo "📁 La aplicación está en: dist/EDF_CatalogoDeTablas/"
    echo "🚀 Para ejecutar: ./dist/EDF_CatalogoDeTablas/EDF_CatalogoDeTablas"
    
else
    echo "❌ Error: La aplicación no se construyó correctamente"
    exit 1
fi
