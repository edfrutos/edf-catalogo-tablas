#!/bin/bash

# Script para crear DMG de la aplicación nativa con WebSockets
# EDF Catálogo de Tablas - Aplicación Nativa WebSockets

set -e

echo "💿 Creando DMG para aplicación nativa con WebSockets..."
echo "=" * 60

# Variables
APP_NAME="EDF_CatalogoDeTablas_Web_Native"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
DMG_PATH="dist/${DMG_NAME}"
VOLUME_NAME="EDF Catálogo de Tablas (Web Nativa)"
TEMP_DIR="/tmp/${APP_NAME}_dmg_temp"

# Verificar que existe la aplicación
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: No se encontró la aplicación en $APP_PATH"
    echo "Ejecuta primero: ./build_native_websockets.sh"
    exit 1
fi

echo "✅ Aplicación encontrada: $APP_PATH"

# Limpiar directorio temporal si existe
if [ -d "$TEMP_DIR" ]; then
    echo "🧹 Limpiando directorio temporal..."
    rm -rf "$TEMP_DIR"
fi

# Crear directorio temporal
echo "📁 Creando directorio temporal..."
mkdir -p "$TEMP_DIR"

# Copiar aplicación al directorio temporal
echo "📋 Copiando aplicación..."
cp -R "$APP_PATH" "$TEMP_DIR/"

# Crear enlace simbólico a Aplicaciones
echo "🔗 Creando enlace a Aplicaciones..."
ln -s /Applications "$TEMP_DIR/Aplicaciones"

# Crear archivo de información
echo "📄 Creando archivo de información..."
cat > "$TEMP_DIR/INFORMACION.txt" << 'EOF'
EDF Catálogo de Tablas - Aplicación Web Nativa
==============================================

🎯 DESCRIPCIÓN:
Esta es una aplicación nativa de macOS que ejecuta tu aplicación
web Flask completa en una ventana nativa sin navegador externo.

🚀 CARACTERÍSTICAS:
• Aplicación nativa de macOS (.app)
• Icono personalizado de EDF
• Interfaz web completa en ventana nativa
• Comunicación WebSockets en tiempo real
• Sin dependencia de navegador externo
• Misma funcionalidad que la aplicación web
• Gestión completa de catálogos
• Administración de usuarios
• Herramientas de mantenimiento

📋 FUNCIONALIDADES:
• Gestión de catálogos de productos
• Administración de usuarios y permisos
• Importación/exportación de datos
• Backup y restauración del sistema
• Diagnóstico y logs
• Configuración avanzada

🌐 INTERFAZ WEB NATIVA:
• Aplicación web Flask completa en ventana nativa
• Comunicación WebSockets en tiempo real
• Actualizaciones automáticas
• Sin dependencia de navegador externo
• Misma experiencia que la aplicación web

💻 REQUISITOS DEL SISTEMA:
• macOS 10.15 (Catalina) o superior
• 4GB RAM mínimo
• 500MB espacio en disco
• Conexión a internet para WebSockets

📦 INSTALACIÓN:
1. Arrastra la aplicación a la carpeta "Aplicaciones"
2. Ejecuta la aplicación desde Finder
3. La aplicación se conectará automáticamente via WebSockets

🔧 CONFIGURACIÓN:
• La aplicación se configura automáticamente
• Los logs se guardan en ~/Library/Logs/
• La configuración se guarda en ~/Library/Preferences/

📞 SOPORTE:
• Email: soporte@edf.com
• Teléfono: +34 123 456 789
• Horario: L-V 9:00-18:00

🔄 ACTUALIZACIONES:
• Las actualizaciones se descargan automáticamente
• Se notifican nuevas versiones via WebSockets
• Instalación con un clic desde la aplicación

© 2025 EDF Catálogo de Tablas
Versión: 1.0.0 (Web Nativa)
EOF

# Crear DMG
echo "💿 Creando DMG..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_PATH"

# Verificar que se creó el DMG
if [ ! -f "$DMG_PATH" ]; then
    echo "❌ Error: No se pudo crear el DMG"
    exit 1
fi

# Limpiar directorio temporal
echo "🧹 Limpiando directorio temporal..."
rm -rf "$TEMP_DIR"

# Mostrar información del DMG
echo "✅ DMG creado exitosamente"
echo "📁 Ubicación: $DMG_PATH"
echo "📏 Tamaño: $(du -h "$DMG_PATH" | cut -f1)"

# Verificar integridad del DMG
echo "🔍 Verificando integridad del DMG..."
if hdiutil verify "$DMG_PATH" > /dev/null 2>&1; then
    echo "✅ DMG verificado correctamente"
else
    echo "⚠️  Advertencia: No se pudo verificar el DMG"
fi

echo ""
echo "🎉 ¡DMG creado exitosamente!"
echo "💿 Archivo: $DMG_PATH"
echo "📱 Para instalar:"
echo "   1. Abre el DMG haciendo doble clic"
echo "   2. Arrastra la aplicación a la carpeta 'Aplicaciones'"
echo "   3. Ejecuta la aplicación desde Finder"
echo ""
echo "🚀 La aplicación ejecutará tu aplicación web Flask completa"
echo "   en una ventana nativa sin necesidad de navegador externo."
