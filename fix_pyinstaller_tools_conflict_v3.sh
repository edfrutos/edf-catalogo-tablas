#!/bin/bash

# Script para resolver conflictos de PyInstaller con el directorio tools
# Versión 3.0 - Solución completa para GitHub Actions

set -e

echo "🔧 Iniciando limpieza de conflictos PyInstaller..."

# Función para limpiar directorios de build
clean_build_dirs() {
    echo "🧹 Limpiando directorios de build..."
    
    # Limpiar directorios de PyInstaller
    if [ -d "build" ]; then
        echo "  📁 Eliminando directorio build/"
        rm -rf build/
    fi
    
    if [ -d "dist" ]; then
        echo "  📁 Eliminando directorio dist/"
        rm -rf dist/
    fi
    
    # Limpiar archivos .spec temporales
    for spec_file in *.spec.tmp *.spec.backup; do
        if [ -f "$spec_file" ]; then
            echo "  📄 Eliminando archivo temporal: $spec_file"
            rm -f "$spec_file"
        fi
    done
    
    echo "✅ Limpieza de directorios completada"
}

# Función para verificar conflictos en el directorio tools
check_tools_conflicts() {
    echo "🔍 Verificando conflictos en directorio tools..."
    
    if [ -d "tools" ]; then
        echo "  📁 Directorio tools encontrado"
        
        # Verificar si hay archivos con nombres problemáticos
        problematic_files=()
        
        # Buscar archivos que podrían causar conflictos
        while IFS= read -r -d '' file; do
            filename=$(basename "$file")
            if [[ "$filename" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ! "$filename" =~ \. ]]; then
                problematic_files+=("$file")
            fi
        done < <(find tools -type f -print0 2>/dev/null || true)
        
        if [ ${#problematic_files[@]} -gt 0 ]; then
            echo "  ⚠️  Archivos potencialmente problemáticos encontrados:"
            for file in "${problematic_files[@]}"; do
                echo "    - $file"
            done
        else
            echo "  ✅ No se encontraron archivos problemáticos"
        fi
    else
        echo "  ❌ Directorio tools no encontrado"
    fi
}

# Función para crear un .spec limpio
create_clean_spec() {
    echo "📝 Creando archivo .spec limpio..."
    
    # Hacer backup del archivo .spec actual
    if [ -f "EDF_CatalogoDeTablas.spec" ]; then
        cp EDF_CatalogoDeTablas.spec EDF_CatalogoDeTablas.spec.backup.$(date +%Y%m%d_%H%M%S)
        echo "  💾 Backup creado: EDF_CatalogoDeTablas.spec.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Crear un .spec optimizado que evite conflictos
    cat > EDF_CatalogoDeTablas.spec.clean << 'EOF'
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
        # Incluir solo subdirectorios específicos de tools para evitar conflictos
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

    echo "✅ Archivo .spec limpio creado"
}

# Función para aplicar la solución
apply_solution() {
    echo "🔧 Aplicando solución para conflictos PyInstaller..."
    
    # Limpiar directorios de build
    clean_build_dirs
    
    # Verificar conflictos
    check_tools_conflicts
    
    # Crear .spec limpio
    create_clean_spec
    
    # Reemplazar el archivo .spec original
    if [ -f "EDF_CatalogoDeTablas.spec.clean" ]; then
        mv EDF_CatalogoDeTablas.spec.clean EDF_CatalogoDeTablas.spec
        echo "✅ Archivo .spec actualizado"
    fi
    
    echo "🎉 Solución aplicada exitosamente"
}

# Función para verificar el estado
verify_solution() {
    echo "🔍 Verificando estado de la solución..."
    
    if [ -f "EDF_CatalogoDeTablas.spec" ]; then
        echo "  ✅ Archivo .spec presente"
        
        # Verificar que no hay referencias problemáticas
        if grep -q "tools/" EDF_CatalogoDeTablas.spec; then
            echo "  ✅ Referencias a tools/ encontradas (correcto)"
        else
            echo "  ⚠️  No se encontraron referencias a tools/"
        fi
    else
        echo "  ❌ Archivo .spec no encontrado"
        return 1
    fi
    
    echo "✅ Verificación completada"
}

# Función principal
main() {
    echo "🚀 Iniciando script de resolución de conflictos PyInstaller v3.0"
    echo "📅 Fecha: $(date)"
    echo "📁 Directorio actual: $(pwd)"
    
    # Aplicar solución
    apply_solution
    
    # Verificar resultado
    verify_solution
    
    echo "🎯 Script completado exitosamente"
}

# Ejecutar función principal
main "$@"
