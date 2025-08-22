#!/bin/bash

# Script específico para resolver el conflicto del directorio tools en PyInstaller
# Este script se enfoca únicamente en el problema: "there already exists a file at that path"

set -e

echo "🔧 Resolviendo conflicto específico del directorio tools..."

# Función para limpiar completamente los directorios de build
clean_build_directories() {
    echo "🧹 Limpiando directorios de build..."
    
    # Eliminar directorios de PyInstaller
    if [ -d "build" ]; then
        echo "  📁 Eliminando build/"
        rm -rf build/
    fi
    
    if [ -d "dist" ]; then
        echo "  📁 Eliminando dist/"
        rm -rf dist/
    fi
    
    # Eliminar archivos .spec temporales
    for spec_file in *.spec.tmp *.spec.backup; do
        if [ -f "$spec_file" ]; then
            echo "  📄 Eliminando $spec_file"
            rm -f "$spec_file"
        fi
    done
    
    echo "✅ Limpieza de directorios completada"
}

# Función para verificar y resolver conflictos específicos
resolve_tools_conflicts() {
    echo "🔍 Verificando conflictos específicos del directorio tools..."
    
    # Buscar archivos llamados 'tools' (sin extensión) que puedan causar conflictos
    echo "  🔍 Buscando archivos conflictivos..."
    
    # Buscar archivos llamados exactamente 'tools'
    tools_files=$(find . -name "tools" -type f 2>/dev/null || true)
    
    if [ -n "$tools_files" ]; then
        echo "  ⚠️  Archivos 'tools' encontrados (pueden causar conflictos):"
        echo "$tools_files" | while read -r file; do
            echo "    - $file"
        done
        
        echo "  🗑️  Eliminando archivos 'tools' conflictivos..."
        echo "$tools_files" | while read -r file; do
            rm -f "$file"
            echo "    ✅ Eliminado: $file"
        done
    else
        echo "  ✅ No se encontraron archivos 'tools' conflictivos"
    fi
    
    # Verificar si hay un archivo 'tools' en el directorio raíz
    if [ -f "tools" ]; then
        echo "  ⚠️  Archivo 'tools' encontrado en directorio raíz"
        echo "  🗑️  Eliminando archivo 'tools' del directorio raíz..."
        rm -f tools
        echo "    ✅ Archivo 'tools' eliminado del directorio raíz"
    fi
    
    # Verificar si hay un archivo 'tools' en el bundle de la aplicación
    if [ -f "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks/tools" ]; then
        echo "  ⚠️  Archivo 'tools' encontrado en el bundle de la aplicación"
        echo "  🗑️  Eliminando archivo 'tools' del bundle..."
        rm -f "dist/EDF_CatalogoDeTablas.app/Contents/Frameworks/tools"
        echo "    ✅ Archivo 'tools' eliminado del bundle"
    fi
    
    echo "✅ Resolución de conflictos completada"
}

# Función para verificar la estructura del directorio tools
verify_tools_structure() {
    echo "🔍 Verificando estructura del directorio tools..."
    
    if [ -d "tools" ]; then
        echo "  📁 Directorio tools encontrado"
        echo "  📋 Contenido del directorio tools:"
        ls -la tools/ | head -20
        
        # Verificar que tools es un directorio y no un archivo
        if [ -d "tools" ] && [ ! -f "tools" ]; then
            echo "  ✅ tools es un directorio válido"
        else
            echo "  ❌ tools no es un directorio válido"
            return 1
        fi
    else
        echo "  ❌ Directorio tools no encontrado"
        return 1
    fi
    
    echo "✅ Verificación de estructura completada"
}

# Función para crear un .spec optimizado
create_optimized_spec() {
    echo "📝 Creando archivo .spec optimizado..."
    
    # Hacer backup del archivo actual
    if [ -f "EDF_CatalogoDeTablas.spec" ]; then
        backup_name="EDF_CatalogoDeTablas.spec.backup.$(date +%Y%m%d_%H%M%S)"
        cp EDF_CatalogoDeTablas.spec "$backup_name"
        echo "  💾 Backup creado: $backup_name"
    fi
    
    # Crear un .spec que evite el conflicto específico
    cat > EDF_CatalogoDeTablas.spec.optimized << 'EOF'
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
        # Incluir subdirectorios de tools de forma específica para evitar conflictos
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

app = BUNDLE(
    coll,
    name='EDF_CatalogoDeTablas.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'CFBundleName': 'EDF_CatalogoDeTablas',
        'CFBundleDisplayName': 'EDF Catalogo de Tablas',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
EOF

    # Reemplazar el archivo original
    mv EDF_CatalogoDeTablas.spec.optimized EDF_CatalogoDeTablas.spec
    echo "✅ Archivo .spec optimizado creado"
}

# Función principal
main() {
    echo "🚀 Iniciando resolución específica del conflicto tools"
    echo "📅 Fecha: $(date)"
    echo "📁 Directorio actual: $(pwd)"
    
    # Limpiar directorios de build
    clean_build_directories
    
    # Verificar estructura del directorio tools
    verify_tools_structure
    
    # Resolver conflictos específicos
    resolve_tools_conflicts
    
    # Crear .spec optimizado
    create_optimized_spec
    
    echo "🎯 Resolución del conflicto tools completada"
    echo "✅ El proyecto está listo para el build de PyInstaller"
}

# Ejecutar función principal
main "$@"
