#!/bin/bash

echo "🚀 Construyendo EDF Catálogo de Tablas (Versión Nativa)"
echo "====================================================="

# Verificar que pywebview esté instalado
echo "🔍 Verificando dependencias..."
if ! python3 -c "import webview" 2>/dev/null; then
    echo "❌ PyWebView no está instalado. Instalando..."
    pip install pywebview
fi

# Verificar que el icono existe
echo "🎨 Verificando icono de la aplicación..."
if [ ! -f "app/static/favicon.icns" ]; then
    echo "❌ Icono no encontrado en app/static/favicon.icns"
    exit 1
fi
echo "✅ Icono encontrado: app/static/favicon.icns"

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf build/ dist/

# Crear el archivo .spec para la versión nativa con configuración de macOS
echo "📝 Generando archivo de especificación..."
cat > EDF_CatalogoDeTablas_Native.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher_native.py'],
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
        # Solo incluir directorios esenciales para evitar conflictos
        ('backups', 'backups'),
        ('uploads', 'uploads'),
        ('flask_session', 'flask_session'),
        ('instance', 'instance'),
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
        'webview',
        'threading',
        'webbrowser',
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
    name='EDF_CatalogoDeTablas_Native',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sin consola para aplicación nativa
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/static/favicon.icns',  # Icono de la aplicación
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDF_CatalogoDeTablas_Native',
)

# Crear aplicación .app de macOS
app = BUNDLE(
    coll,
    name='EDF_CatalogoDeTablas_Native.app',
    icon='app/static/favicon.icns',
    bundle_identifier='com.edefrutos.catalogotablas',
    info_plist={
        'CFBundleName': 'EDF Catálogo de Tablas',
        'CFBundleDisplayName': 'EDF Catálogo de Tablas',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,
    },
)
EOF

# Construir la aplicación
echo "🔨 Construyendo aplicación nativa con PyInstaller..."
pyinstaller --clean EDF_CatalogoDeTablas_Native.spec

if [ $? -eq 0 ]; then
    echo "✅ Construcción completada exitosamente!"
    echo "📁 Aplicación disponible en: dist/EDF_CatalogoDeTablas_Native.app/"
    echo "🚀 Para ejecutar: open dist/EDF_CatalogoDeTablas_Native.app"
    echo "🖥️  Esta versión se ejecuta en una ventana nativa de macOS"
    echo "🎨 Icono aplicado: app/static/favicon.icns"
    echo "📱 Ahora puedes ejecutar desde Finder haciendo doble clic en la aplicación"
else
    echo "❌ Error en la construcción"
    exit 1
fi
