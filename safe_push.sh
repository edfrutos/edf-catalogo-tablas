#!/bin/bash

# Script para hacer push de forma segura
# Ejecuta verificaciones antes de hacer push

echo "🚀 SAFE PUSH - PUSH SEGURO"
echo "=========================="

# Verificar que estamos en la rama correcta
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Estás en la rama: $CURRENT_BRANCH"
    echo "💡 Considera hacer push a main: git checkout main"
    read -p "¿Continuar con push a $CURRENT_BRANCH? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Push cancelado"
        exit 1
    fi
fi

# Ejecutar verificaciones
echo ""
echo "🔍 Ejecutando verificaciones previas..."
if ! ./verify_build_files.sh; then
    echo "❌ Verificaciones fallaron"
    echo "🚫 Push cancelado"
    exit 1
fi

# Verificar estado de git
echo ""
echo "📋 Verificando estado de git..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Hay cambios sin commitear:"
    git status --short
    read -p "¿Hacer commit de los cambios? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Haciendo commit automático..."
        git add .
        git commit -m "🔧 AUTO: Cambios automáticos antes del push"
    else
        echo "❌ Push cancelado - Haz commit manualmente"
        exit 1
    fi
else
    echo "✅ No hay cambios pendientes"
fi

# Verificar que hay commits para hacer push
if [ "$(git rev-list HEAD...origin/main --count)" -eq 0 ]; then
    echo "⚠️  No hay commits nuevos para hacer push"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Push cancelado"
        exit 1
    fi
fi

# Hacer push
echo ""
echo "🚀 Haciendo push..."
if git push origin "$CURRENT_BRANCH"; then
    echo "✅ Push exitoso!"
    echo "🎉 Código subido correctamente"
else
    echo "❌ Push falló"
    exit 1
fi

echo ""
echo "📊 RESUMEN"
echo "=========="
echo "✅ Verificaciones completadas"
echo "✅ Push exitoso a $CURRENT_BRANCH"
echo "🎉 ¡Todo listo!"
