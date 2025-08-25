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
if [ -f "EDF_CatalogoDeTablas_Native_WebSockets.spec" ]; then
    echo "✅ Archivo .spec existente encontrado, usando el existente..."
else
    echo "❌ Error: No se encuentra el archivo EDF_CatalogoDeTablas_Native_WebSockets.spec"
    echo "🔧 Creando archivo .spec básico..."
    cat > EDF_CatalogoDeTablas_Native_WebSockets.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher_native_websockets.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('config.py', '.'),
        ('wsgi.py', '.'),
        ('.env', '.'),
        ('requirements.txt', '.'),
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
    name='EDF_CatalogoDeTablas_Web_Native',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='EDF_CatalogoDeTablas_Web_Native',
)

app = BUNDLE(
    coll,
    name='EDF_CatalogoDeTablas_Web_Native.app',
    icon=None,
    bundle_identifier='com.edefrutos.catalogodetablas.websockets',
    info_plist={
        'CFBundleName': 'EDF Catálogo de Tablas WebSockets',
        'CFBundleDisplayName': 'EDF Catálogo de Tablas',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'EDF_CatalogoDeTablas_Web_Native',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
    },
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
pyinstaller --clean EDF_CatalogoDeTablas_Native_WebSockets.spec

# Verificar que la aplicación se construyó correctamente
if [ -d "dist/EDF_CatalogoDeTablas_Web_Native.app" ]; then
    echo "✅ Aplicación construida exitosamente en dist/EDF_CatalogoDeTablas_Web_Native.app/"
    
    # Mostrar información de la aplicación
    echo "📊 Información de la aplicación:"
    du -sh dist/EDF_CatalogoDeTablas_Web_Native.app/
    ls -la dist/EDF_CatalogoDeTablas_Web_Native.app/Contents/MacOS/
    
    echo ""
    echo "🎉 ¡Construcción completada!"
    echo "📁 La aplicación está en: dist/EDF_CatalogoDeTablas_Web_Native.app/"
    echo "🚀 Para ejecutar: open dist/EDF_CatalogoDeTablas_Web_Native.app"
    
else
    echo "❌ Error: La aplicación no se construyó correctamente"
    exit 1
fi
