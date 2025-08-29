#!/bin/bash

# Script para crear DMG de la aplicación nativa con WebSockets
# EDF Catálogo de Tablas - Aplicación Nativa Finder

set -e

echo "💿 Creando DMG para aplicación nativa Finder..."
echo "============================================================"

# Variables
APP_NAME="EDF_CatalogoDeTablas_Native_Finder"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
DMG_PATH="dist/${DMG_NAME}"
VOLUME_NAME="EDF Catálogo de Tablas (Finder Nativo)"
TEMP_DIR="/tmp/${APP_NAME}_dmg_temp"

# Verificar que existe la aplicación
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: No se encontró la aplicación en $APP_PATH"
    echo "Ejecuta primero: ./build_native_finder.sh"
    exit 1
fi

echo "✅ Aplicación encontrada: $APP_PATH"

# Verificar que el icono esté incluido
ICON_PATH="dist/${APP_NAME}.app/Contents/Resources/edf_developer.icns"
if [ -f "$ICON_PATH" ]; then
    echo "✅ Icono personalizado encontrado: $ICON_PATH"
else
    echo "⚠️  Advertencia: Icono personalizado no encontrado"
fi

# Verificar que el archivo .env esté incluido
ENV_PATH="dist/${APP_NAME}.app/Contents/Resources/.env"
if [ -f "$ENV_PATH" ]; then
    echo "✅ Archivo .env encontrado: $ENV_PATH"
else
    echo "⚠️  Advertencia: Archivo .env no encontrado"
fi

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
EDF Catálogo de Tablas - Aplicación Nativa Finder
=================================================

🎯 DESCRIPCIÓN:
Esta es una aplicación nativa de macOS que ejecuta tu aplicación
web Flask completa en una ventana nativa tipo Finder sin navegador externo.

🚀 CARACTERÍSTICAS:
• Aplicación nativa de macOS (.app)
• Icono personalizado de EDF Developer
• Ventana nativa tipo Finder
• Interfaz web completa en ventana nativa
• Comunicación WebSockets en tiempo real
• Sin dependencia de navegador externo
• Misma funcionalidad que la aplicación web
• Gestión completa de catálogos
• Administración de usuarios
• Herramientas de mantenimiento
• Conexión a MongoDB Atlas

📋 FUNCIONALIDADES:
• Gestión de catálogos de productos
• Administración de usuarios y permisos
• Importación/exportación de datos
• Backup y restauración del sistema
• Diagnóstico y logs
• Configuración avanzada
• Conexión a base de datos MongoDB Atlas
• Sistema de autenticación completo

🌐 INTERFAZ NATIVA:
• Aplicación web Flask completa en ventana nativa
• Ventana tipo Finder (no navegador)
• Comunicación WebSockets en tiempo real
• Actualizaciones automáticas
• Sin dependencia de navegador externo
• Misma experiencia que la aplicación web
• Icono personalizado visible en todo el sistema

💻 REQUISITOS DEL SISTEMA:
• macOS 10.13 (High Sierra) o superior
• 4GB RAM mínimo
• 500MB espacio en disco
• Conexión a internet para MongoDB Atlas y WebSockets

📦 INSTALACIÓN:
1. Arrastra la aplicación a la carpeta "Aplicaciones"
2. Ejecuta la aplicación desde Finder
3. La aplicación se conectará automáticamente a MongoDB Atlas
4. Inicia sesión con tus credenciales

🔧 CONFIGURACIÓN:
• La aplicación se configura automáticamente
• Variables de entorno incluidas en el paquete
• Conexión a MongoDB Atlas configurada
• Los logs se guardan en directorio temporal
• La configuración se guarda automáticamente

🔐 AUTENTICACIÓN:
• Sistema de login completo
• Redirección automática según rol (admin/user)
• Sesiones persistentes
• Gestión de permisos

📊 BASE DE DATOS:
• Conexión a MongoDB Atlas
• Configuración automática
• Backup y restauración
• Gestión de datos en la nube

📞 SOPORTE:
• Email: soporte@edf.com
• Teléfono: +34 123 456 789
• Horario: L-V 9:00-18:00

🔄 ACTUALIZACIONES:
• Las actualizaciones se descargan automáticamente
• Se notifican nuevas versiones via WebSockets
• Instalación con un clic desde la aplicación

🎨 ICONO PERSONALIZADO:
• Icono de EDF Developer incluido
• Visible en Finder, Dock, Launchpad y Spotlight
• Configuración nativa de macOS

© 2025 EDF Developer
Versión: 1.0.0 (Finder Nativo)
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

# Mostrar información adicional
echo ""
echo "🎉 ¡DMG creado exitosamente!"
echo "💿 Archivo: $DMG_PATH"
echo "📱 Para instalar:"
echo "   1. Abre el DMG haciendo doble clic"
echo "   2. Arrastra la aplicación a la carpeta 'Aplicaciones'"
echo "   3. Ejecuta la aplicación desde Finder"
echo ""
echo "🚀 La aplicación ejecutará tu aplicación web Flask completa"
echo "   en una ventana nativa tipo Finder sin necesidad de navegador externo."
echo ""
echo "🎨 Características especiales:"
echo "   • Icono personalizado de EDF Developer"
echo "   • Conexión automática a MongoDB Atlas"
echo "   • Sistema de autenticación completo"
echo "   • Ventana nativa tipo Finder"
echo ""
echo "🔧 Para probar la aplicación:"
echo "   python test_native_app_env.py"
