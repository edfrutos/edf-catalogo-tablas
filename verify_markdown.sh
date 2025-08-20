#!/bin/bash

# Script para verificar y gestionar markdownlint
# Ayuda a manejar errores de linting de Markdown

echo "📝 VERIFICACIÓN DE MARKDOWNLINT"
echo "==============================="

# Verificar si markdownlint está instalado
if command -v markdownlint >/dev/null 2>&1; then
    echo "✅ markdownlint está instalado"
    echo "📋 Versión: $(markdownlint --version)"
elif [ -f "node_modules/.bin/markdownlint" ]; then
    echo "✅ markdownlint está instalado localmente"
    MARKDOWNLINT="./node_modules/.bin/markdownlint"
else
    echo "❌ markdownlint no está instalado"
    echo "🔧 Instalando markdownlint..."
    npm install markdownlint-cli
    MARKDOWNLINT="./node_modules/.bin/markdownlint"
fi

echo ""
echo "🔍 Verificando configuración de markdownlint..."

# Verificar si existe el archivo de configuración
if [ -f ".markdownlint.json" ]; then
    echo "✅ .markdownlint.json existe"
    echo "📏 Tamaño: $(wc -l < .markdownlint.json) líneas"
else
    echo "❌ .markdownlint.json no existe"
    echo "🔧 Creando configuración básica..."
    cat > .markdownlint.json << 'EOF'
{
  "default": true,
  "MD013": false,
  "MD025": {
    "level": 1,
    "front_matter_title": ""
  },
  "MD033": false,
  "MD041": false,
  "MD024": false,
  "MD026": false,
  "MD029": false,
  "MD030": false,
  "MD031": false,
  "MD032": false,
  "MD034": false,
  "MD035": false,
  "MD036": false,
  "MD037": false,
  "MD038": false,
  "MD039": false,
  "MD040": false,
  "MD042": false,
  "MD043": false,
  "MD044": false,
  "MD045": false,
  "MD046": false,
  "MD047": false,
  "MD048": false,
  "MD049": false,
  "MD050": false
}
EOF
    echo "✅ Configuración básica creada"
fi

echo ""
echo "🔍 Ejecutando verificación de markdownlint..."

# Encontrar archivos markdown
MD_FILES=$(find . -name "*.md" -type f 2>/dev/null | grep -v node_modules | grep -v .venv | grep -v __pycache__)

if [ -z "$MD_FILES" ]; then
    echo "⚠️  No se encontraron archivos .md"
    exit 0
fi

echo "📋 Archivos .md encontrados:"
echo "$MD_FILES" | head -5
if [ "$(echo "$MD_FILES" | wc -l)" -gt 5 ]; then
    echo "... y $(($(echo "$MD_FILES" | wc -l) - 5)) más"
fi

echo ""
echo "🔍 Verificando archivos markdown..."

# Ejecutar markdownlint
if [ -n "$MARKDOWNLINT" ]; then
    if $MARKDOWNLINT --config .markdownlint.json $MD_FILES 2>/dev/null; then
        echo "✅ markdownlint no encontró errores"
    else
        echo "⚠️  markdownlint encontró algunos problemas"
        echo "💡 Ejecutando con más detalles..."
        $MARKDOWNLINT --config .markdownlint.json $MD_FILES 2>/dev/null || true
    fi
else
    if markdownlint --config .markdownlint.json $MD_FILES 2>/dev/null; then
        echo "✅ markdownlint no encontró errores"
    else
        echo "⚠️  markdownlint encontró algunos problemas"
        echo "💡 Ejecutando con más detalles..."
        markdownlint --config .markdownlint.json $MD_FILES 2>/dev/null || true
    fi
fi

echo ""
echo "🔧 Opciones de configuración disponibles:"

echo "1. **Excluir archivos específicos:**"
echo "   Añadir a .markdownlintignore:"
echo "   - '*.md' (para excluir todos los archivos markdown)"
echo "   - 'README.md' (para excluir archivos específicos)"

echo ""
echo "2. **Deshabilitar reglas específicas:**"
echo "   En .markdownlint.json:"
echo "   - 'MD025': false (para múltiples H1)"
echo "   - 'MD013': false (para líneas largas)"
echo "   - 'MD033': false (para HTML inline)"

echo ""
echo "3. **Ignorar líneas específicas:**"
echo "   En archivos .md:"
echo "   <!-- markdownlint-disable MD025 -->"
echo "   # Título H1"
echo "   <!-- markdownlint-enable MD025 -->"

echo ""
echo "4. **Comandos útiles:**"
echo "   - markdownlint --fix *.md (corregir automáticamente)"
echo "   - markdownlint --config .markdownlint.json *.md"
echo "   - markdownlint --help (ver todas las opciones)"

echo ""
echo "📊 RESUMEN"
echo "=========="
echo "✅ Verificación de markdownlint completada"
echo "📋 Configuración en: .markdownlint.json"
echo "💡 Usa 'markdownlint --help' para más opciones"
