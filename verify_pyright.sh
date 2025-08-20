#!/bin/bash

# Script para verificar y configurar Pyright
# Ayuda a manejar errores de linting de Python

echo "🐍 VERIFICACIÓN DE PYRIGHT"
echo "=========================="

# Verificar si pyright está instalado
if command -v pyright >/dev/null 2>&1; then
    echo "✅ Pyright está instalado"
    echo "📋 Versión: $(pyright --version)"
else
    echo "❌ Pyright no está instalado"
    echo "🔧 Instalando Pyright..."
    pip install pyright
fi

echo ""
echo "🔍 Verificando configuración de Pyright..."

# Verificar si existe el archivo de configuración
if [ -f "pyrightconfig.json" ]; then
    echo "✅ pyrightconfig.json existe"
    echo "📏 Tamaño: $(wc -l < pyrightconfig.json) líneas"
else
    echo "❌ pyrightconfig.json no existe"
    echo "🔧 Creando configuración básica..."
    cat > pyrightconfig.json << 'EOF'
{
    "venvPath": ".",
    "venv": ".venv",
    "pythonVersion": "3.8",
    "pythonPlatform": "Darwin",
    "include": [
        "app",
        "tools",
        "scripts"
    ],
    "exclude": [
        "**/node_modules",
        "**/__pycache__",
        ".venv",
        "dist",
        "build"
    ],
    "ignore": [
        "**/migrations",
        "**/tests"
    ],
    "reportMissingImports": "warning",
    "reportMissingTypeStubs": false,
    "reportUnboundVariable": "warning",
    "reportPossiblyUnboundVariable": "warning",
    "reportUnusedImport": "warning",
    "reportUnusedVariable": "warning"
}
EOF
    echo "✅ Configuración básica creada"
fi

echo ""
echo "🔍 Ejecutando verificación de Pyright..."

# Ejecutar Pyright con configuración específica
if pyright --outputformat=text 2>/dev/null; then
    echo "✅ Pyright no encontró errores críticos"
else
    echo "⚠️  Pyright encontró algunos problemas"
    echo "💡 Ejecutando con más detalles..."
    pyright --outputformat=text --level=warning 2>/dev/null || true
fi

echo ""
echo "🔧 Opciones de configuración disponibles:"

echo "1. **Excluir archivos específicos:**"
echo "   Añadir a 'exclude' en pyrightconfig.json:"
echo "   - 'launcher_web.py'"
echo "   - '*.py' (para excluir todos los archivos Python)"

echo ""
echo "2. **Cambiar nivel de severidad:**"
echo "   - 'error' -> 'warning' -> 'information' -> 'none'"

echo ""
echo "3. **Ignorar tipos específicos de errores:**"
echo "   - reportUnboundVariable: 'none'"
echo "   - reportPossiblyUnboundVariable: 'none'"
echo "   - reportUnusedImport: 'none'"

echo ""
echo "4. **Añadir comentarios de supresión:**"
echo "   # pyright: reportUnboundVariable=false"
echo "   # pyright: reportPossiblyUnboundVariable=false"

echo ""
echo "📊 RESUMEN"
echo "=========="
echo "✅ Verificación de Pyright completada"
echo "📋 Configuración en: pyrightconfig.json"
echo "💡 Usa 'pyright --help' para más opciones"
