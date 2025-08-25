#!/bin/bash

# Script para verificar y crear EDF_CatalogoDeTablas.spec
# Soluciona el problema del workflow de GitHub Actions

echo "📋 VERIFICACIÓN DE ARCHIVO .SPEC"
echo "================================"

SPEC_FILE="EDF_CatalogoDeTablas_Native_WebSockets.spec"
BACKUP_FILES=("EDF_CatalogoDeTablas.spec" "EDF_CatalogoDeTablas_Native.spec" "EDF_CatalogoDeTablas_Web.spec")

echo "🔍 Verificando archivo $SPEC_FILE..."

# Verificar si el archivo existe
if [ -f "$SPEC_FILE" ]; then
    echo "✅ $SPEC_FILE existe"
    echo "📏 Tamaño: $(wc -l < "$SPEC_FILE") líneas"
    echo "📋 Primeras 5 líneas:"
    head -5 "$SPEC_FILE"
    exit 0
fi

echo "❌ $SPEC_FILE no encontrado"
echo "🔧 Intentando crear el archivo..."

# Verificar si existen archivos de backup
for backup_file in "${BACKUP_FILES[@]}"; do
    if [ -f "$backup_file" ]; then
        echo "📋 Copiando $backup_file a $SPEC_FILE..."
        cp "$backup_file" "$SPEC_FILE"
        echo "✅ Archivo creado desde $backup_file"
        echo "📏 Tamaño: $(wc -l < "$SPEC_FILE") líneas"
        exit 0
    fi
done

echo "❌ Ningún archivo .spec de backup encontrado"
echo "🔧 Creando archivo $SPEC_FILE básico..."

# Crear archivo .spec básico
cat > "$SPEC_FILE" << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
        ('app/routes', 'app/routes'),
        ('tools', 'tools'),
        ('config', 'config'),
        ('requirements_python310.txt', '.'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'flask',
        'pymongo',
        'boto3',
        'pandas',
        'openpyxl',
        'dotenv',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'cryptography',
        'PIL',
        'psutil',
        'pywebview',
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

app = BUNDLE(
    coll,
    name='EDF_CatalogoDeTablas.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'CFBundleName': 'EDF Catálogo de Tablas',
        'CFBundleDisplayName': 'EDF Catálogo de Tablas',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
EOF

echo "✅ Archivo $SPEC_FILE creado con configuración básica"
echo "📏 Tamaño: $(wc -l < "$SPEC_FILE") líneas"
echo "📋 Primeras 10 líneas:"
head -10 "$SPEC_FILE"

echo ""
echo "📊 RESUMEN"
echo "=========="
echo "✅ Archivo $SPEC_FILE creado/verificado"
echo "📋 Configuración incluida: Flask, MongoDB, AWS, pandas, etc."
echo "🎯 Listo para el workflow de GitHub Actions"
