#!/bin/bash

# Script para capturar notas de chat con Kiro
# Uso: ./capturar-chat.sh "título de la conversación"

FECHA=$(date '+%d/%m/%Y %H:%M')
ARCHIVO="docs/conversaciones/chat-$(date '+%Y%m%d-%H%M').md"

# Crear archivo con encabezado
cat > "$ARCHIVO" << EOF
# Chat con Kiro - $1

**Fecha**: $FECHA  
**Tema**: $1

## 📝 Resumen de la Conversación

<!-- Pegar aquí el contenido del chat -->

## 🔧 Acciones Realizadas

- [ ] Acción 1
- [ ] Acción 2

## 📋 Archivos Modificados

- \`archivo1.ext\` - Descripción del cambio
- \`archivo2.ext\` - Descripción del cambio

## 💡 Notas Importantes

<!-- Puntos clave para recordar -->

---
*Generado automáticamente el $FECHA*
EOF

echo "✅ Archivo creado: $ARCHIVO"
echo "📝 Puedes editarlo para añadir el contenido del chat"