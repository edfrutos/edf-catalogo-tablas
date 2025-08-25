#!/bin/bash

# Script de verificación para archivos necesarios del build
# Ejecutar antes de hacer push para verificar que todo está correcto

echo "🔍 VERIFICACIÓN DE ARCHIVOS PARA BUILD"
echo "======================================"

# Lista de archivos críticos para el build
CRITICAL_FILES=(
    "EDF_CatalogoDeTablas_Native_WebSockets.spec"
    "requirements_python310.txt"
    "run_server.py"
    "app/__init__.py"
    "app/routes/admin_routes.py"
    "app/routes/catalogs_routes.py"
)

# Lista de archivos de backup para .spec
SPEC_BACKUP_FILES=(
    "EDF_CatalogoDeTablas.spec"
    "EDF_CatalogoDeTablas_Native.spec"
    "EDF_CatalogoDeTablas_Web.spec"
)

# Lista de directorios críticos
CRITICAL_DIRS=(
    "app"
    "app/routes"
    "app/templates"
    "app/static"
    "tools"
)

ERRORS=0

echo ""
echo "📋 Verificando archivos críticos..."
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - EXISTE"
    else
        echo "❌ $file - NO EXISTE"
        
        # Intentar crear archivo .spec si no existe
        if [ "$file" = "EDF_CatalogoDeTablas_Native_WebSockets.spec" ]; then
            echo "🔧 Intentando crear $file desde archivos de backup..."
            created=false
            for backup_file in "${SPEC_BACKUP_FILES[@]}"; do
                if [ -f "$backup_file" ]; then
                    echo "📋 Copiando $backup_file a $file..."
                    cp "$backup_file" "$file"
                    echo "✅ $file creado desde $backup_file"
                    created=true
                    break
                fi
            done
            if [ "$created" = false ]; then
                echo "❌ No se pudo crear $file - no hay archivos de backup"
                ERRORS=$((ERRORS + 1))
            fi
        else
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

echo ""
echo "📁 Verificando directorios críticos..."
for dir in "${CRITICAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/ - EXISTE"
    else
        echo "❌ $dir/ - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "🔧 Verificando archivos de configuración..."
CONFIG_FILES=(
    ".github/workflows/build_macos_app.yml"
    "pyproject.toml"
    "pyrightconfig.json"
    "cspell.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - EXISTE"
    else
        echo "❌ $file - NO EXISTE"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "📦 Verificando sintaxis de requirements..."
if python3 -c "import pkg_resources; pkg_resources.parse_requirements(open('requirements_python310.txt'))" 2>/dev/null; then
    echo "✅ requirements_python310.txt - SINTAXIS VÁLIDA"
else
    echo "❌ requirements_python310.txt - ERROR DE SINTAXIS"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "🐍 Verificando sintaxis de Python..."
PYTHON_FILES=$(find app tools scripts -name "*.py" -type f 2>/dev/null | head -10)
for file in $PYTHON_FILES; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✅ $file - SINTAXIS VÁLIDA"
    else
        echo "❌ $file - ERROR DE SINTAXIS"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "🌐 Verificando conectividad básica..."
if ping -c 3 pypi.org > /dev/null 2>&1; then
    echo "✅ PyPI - ACCESIBLE"
else
    echo "❌ PyPI - NO ACCESIBLE"
    ERRORS=$((ERRORS + 1))
fi

if ping -c 3 github.com > /dev/null 2>&1; then
    echo "✅ GitHub - ACCESIBLE"
else
    echo "❌ GitHub - NO ACCESIBLE"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "=========================="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 TODOS LOS ARCHIVOS ESTÁN CORRECTOS"
    echo "✅ Puedes hacer push con confianza"
    exit 0
else
    echo "⚠️  SE ENCONTRARON $ERRORS ERROR(ES)"
    echo "❌ Corrige los errores antes de hacer push"
    exit 1
fi
