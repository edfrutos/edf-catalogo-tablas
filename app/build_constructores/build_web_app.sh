#!/bin/bash

echo "🚀 Construyendo EDF Catálogo de Tablas (Versión Web)"
echo "=================================================="

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf build/ dist/

# Crear el archivo .spec para la versión web
echo "📝 Generando archivo de especificación..."
cat > EDF_CatalogoDeTablas_Web.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher_web.py'],
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
        'PIL',
        'cryptography',
        'bcrypt',
        'webbrowser',
        'threading',
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
    name='EDF_CatalogoDeTablas_Web',
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
    name='EDF_CatalogoDeTablas_Web',
)
EOF

# Construir la aplicación
echo "🔨 Construyendo aplicación con PyInstaller..."
pyinstaller --clean EDF_CatalogoDeTablas_Web.spec

if [ $? -eq 0 ]; then
    echo "✅ Construcción completada exitosamente!"
    echo "📁 Aplicación disponible en: dist/EDF_CatalogoDeTablas_Web/"
    echo "🚀 Para ejecutar: ./dist/EDF_CatalogoDeTablas_Web/EDF_CatalogoDeTablas_Web"
else
    echo "❌ Error en la construcción"
    exit 1
fi
