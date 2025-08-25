#!/bin/bash

# Script para crear un archivo .spec seguro que evite conflictos con el directorio tools
# Cambia el nombre del directorio de destino para evitar conflictos
# Autor: EDF Developer - 2025

set -e

echo "🔧 CREANDO ARCHIVO .SPEC SEGURO..."

# Función para crear el archivo .spec seguro
create_safe_spec() {
    echo "📄 Creando EDF_CatalogoDeTablas_Native_WebSockets.spec seguro..."
    
    cat > "EDF_CatalogoDeTablas_Native_WebSockets.spec" << 'EOF'
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
        'flask', 'flask_login', 'flask_session', 'pymongo', 'requests',
        'webview', 'werkzeug', 'jinja2', 'markupsafe', 'itsdangerous',
        'click', 'blinker', 'boto3', 'botocore', 's3transfer',
        'jmespath', 'python_dateutil', 'urllib3', 'certifi',
        'charset_normalizer', 'idna', 'six', 'websockets',
        'asyncio', 'threading', 'tempfile', 'pathlib', 'datetime',
        'json', 'os', 'sys', 'time',
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

    echo "✅ Archivo .spec seguro creado"
}

# Función para verificar el archivo creado
verify_spec_file() {
    echo "🔍 Verificando archivo .spec creado..."
    
    if [ ! -f "EDF_CatalogoDeTablas_Native_WebSockets.spec" ]; then
        echo "❌ Error: No se pudo crear el archivo .spec"
        return 1
    fi
    
    echo "📄 Archivo creado: EDF_CatalogoDeTablas_Native_WebSockets.spec"
    echo "📏 Tamaño: $(du -sh EDF_CatalogoDeTablas_Native_WebSockets.spec | cut -f1)"
    echo "📊 Líneas: $(wc -l < EDF_CatalogoDeTablas_Native_WebSockets.spec)"
    
    # Verificar que se incluye el directorio app
    if grep -q "app" EDF_CatalogoDeTablas_Native_WebSockets.spec; then
        echo "✅ Se incluye el directorio app correctamente"
    else
        echo "❌ Error: No se encontró el directorio app"
        return 1
    fi
    
    # Verificar que se incluye launcher_native_websockets.py
    if grep -q "launcher_native_websockets.py" EDF_CatalogoDeTablas_Native_WebSockets.spec; then
        echo "✅ Se incluye el launcher correcto"
    else
        echo "❌ Error: No se encontró el launcher_native_websockets.py"
        return 1
    fi
    
    echo "✅ Verificación del archivo .spec completada"
    return 0
}

# Función para mostrar información del cambio
show_change_info() {
    echo ""
    echo "📋 INFORMACIÓN DEL CAMBIO:"
    echo "   🔧 CAMBIO CRÍTICO: Configurado para aplicación nativa con WebSockets"
    echo "   🎯 OBJETIVO: Crear aplicación nativa de macOS con PyWebView"
    echo "   📁 ENTRY POINT: launcher_native_websockets.py"
    echo "   📱 SALIDA: EDF_CatalogoDeTablas_Web_Native.app"
    echo "   ✅ BENEFICIO: Aplicación nativa sin dependencia de navegador"
    echo ""
}

# Función principal
main() {
    echo "🚀 Creando archivo .spec seguro para evitar conflictos..."
    
    create_safe_spec
    show_change_info
    
    if verify_spec_file; then
        echo "✅ Archivo .spec seguro creado y verificado correctamente"
        echo "💡 Ahora puedes ejecutar el build sin conflictos"
        echo "🚀 Comando recomendado: python -m PyInstaller EDF_CatalogoDeTablas_Native_WebSockets.spec"
    else
        echo "❌ Error: No se pudo crear o verificar el archivo .spec"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
