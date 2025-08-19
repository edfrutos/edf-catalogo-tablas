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

# Activar entorno virtual
echo "📦 Activando entorno virtual..."
source .venv/bin/activate

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf build/ dist/ *.spec

# Crear el archivo .spec para PyInstaller
echo "📝 Creando archivo de especificación..."
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
        ('tools', 'tools'),
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
