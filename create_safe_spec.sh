#!/bin/bash

# Script para crear un archivo .spec seguro que evite conflictos con el directorio tools
# Cambia el nombre del directorio de destino para evitar conflictos
# Autor: EDF Developer - 2025

set -e

echo "🔧 CREANDO ARCHIVO .SPEC SEGURO..."

# Función para crear el archivo .spec seguro
create_safe_spec() {
    echo "📄 Creando EDF_CatalogoDeTablas.spec seguro..."
    
    cat > "EDF_CatalogoDeTablas.spec" << 'EOF'
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
        # CAMBIO CRÍTICO: Usar 'app_utils' en lugar de 'app_tools' para evitar conflicto
        ('tools/db_utils', 'app_utils/db_utils'),
        ('tools/utils', 'app_utils/utils'),
        ('tools/maintenance', 'app_utils/maintenance'),
        ('tools/monitoring', 'app_utils/monitoring'),
        ('tools/Admin Utils', 'app_utils/Admin Utils'),
        ('tools/Scripts Principales', 'app_utils/Scripts Principales'),
        ('tools/Users Tools', 'app_utils/Users Tools'),
        ('tools/Test Scripts', 'app_utils/Test Scripts'),
        ('tools/testing', 'app_utils/testing'),
        ('tools/image_utils', 'app_utils/image_utils'),
        ('tools/local', 'app_utils/local'),
        ('tools/macOS', 'app_utils/macOS'),
        ('tools/production', 'app_utils/production'),
        ('tools/system', 'app_utils/system'),
        ('tools/src', 'app_utils/src'),
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
EOF

    echo "✅ Archivo .spec seguro creado"
}

# Función para verificar el archivo creado
verify_spec_file() {
    echo "🔍 Verificando archivo .spec creado..."
    
    if [ ! -f "EDF_CatalogoDeTablas.spec" ]; then
        echo "❌ Error: No se pudo crear el archivo .spec"
        return 1
    fi
    
    echo "📄 Archivo creado: EDF_CatalogoDeTablas.spec"
    echo "📏 Tamaño: $(du -sh EDF_CatalogoDeTablas.spec | cut -f1)"
    echo "📊 Líneas: $(wc -l < EDF_CatalogoDeTablas.spec)"
    
    # Verificar que no hay referencias problemáticas
    if grep -q "app_tools" EDF_CatalogoDeTablas.spec; then
        echo "⚠️  Advertencia: Se encontraron referencias a 'app_tools'"
    else
        echo "✅ No hay referencias problemáticas a 'app_tools'"
    fi
    
    # Verificar que se usan 'app_utils'
    if grep -q "app_utils" EDF_CatalogoDeTablas.spec; then
        echo "✅ Se usan referencias seguras a 'app_utils'"
    else
        echo "❌ Error: No se encontraron referencias a 'app_utils'"
        return 1
    fi
    
    echo "✅ Verificación del archivo .spec completada"
    return 0
}

# Función para mostrar información del cambio
show_change_info() {
    echo ""
    echo "📋 INFORMACIÓN DEL CAMBIO:"
    echo "   🔧 CAMBIO CRÍTICO: Se cambió 'app_tools' por 'app_utils'"
    echo "   🎯 OBJETIVO: Evitar conflicto con el directorio 'tools'"
    echo "   📁 ANTES: tools/ → app_tools/"
    echo "   📁 AHORA: tools/ → app_utils/"
    echo "   ✅ BENEFICIO: No hay conflicto de nombres"
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
        echo "🚀 Comando recomendado: python -m PyInstaller EDF_CatalogoDeTablas.spec"
    else
        echo "❌ Error: No se pudo crear o verificar el archivo .spec"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
