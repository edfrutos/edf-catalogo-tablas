#!/bin/bash

# Script para crear DMG de EDF Catálogo de Tablas (Versión Mejorada)
# Autor: EDF Sistemas
# Fecha: Agosto 2025

set -e

echo "🚀 Creando DMG para EDF Catálogo de Tablas (Versión Mejorada)..."
echo "================================================================"

# Variables
APP_NAME="EDF_CatalogoDeTablas_Improved"
DMG_NAME="${APP_NAME}_macOS_$(date +%Y%m%d_%H%M%S).dmg"
VOLUME_NAME="EDF Catálogo de Tablas (Mejorado)"
APP_PATH="dist/${APP_NAME}.app"
MANUAL_PATH="MANUAL_APLICACION_NATIVA.md"
TEMP_DIR="temp_dmg_improved"
DMG_SIZE="1200m"  # Tamaño del DMG en MB

# Verificar que la aplicación existe
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: No se encuentra la aplicación en $APP_PATH"
    echo "   Ejecuta primero: python -m PyInstaller EDF_CatalogoDeTablas_Native_Improved.spec"
    exit 1
fi

# Verificar que el manual existe
if [ ! -f "$MANUAL_PATH" ]; then
    echo "❌ Error: No se encuentra el manual en $MANUAL_PATH"
    exit 1
fi

echo "✅ Aplicación mejorada encontrada: $APP_PATH"
echo "✅ Manual encontrado: $MANUAL_PATH"

# Limpiar directorio temporal si existe
if [ -d "$TEMP_DIR" ]; then
    echo "🧹 Limpiando directorio temporal..."
    rm -rf "$TEMP_DIR"
fi

# Crear directorio temporal
echo "📁 Creando estructura del DMG..."
mkdir -p "$TEMP_DIR"

# Copiar aplicación
echo "📱 Copiando aplicación mejorada..."
cp -R "$APP_PATH" "$TEMP_DIR/"

# Copiar manual
echo "📖 Copiando manual..."
cp "$MANUAL_PATH" "$TEMP_DIR/"

# Crear enlace a Aplicaciones
echo "🔗 Creando enlace a Aplicaciones..."
ln -s /Applications "$TEMP_DIR/Aplicaciones"

# Crear archivo de información adicional
cat > "$TEMP_DIR/INFORMACION_MEJORADA.txt" << 'EOF'
EDF Catálogo de Tablas - Aplicación Nativa de macOS (Versión Mejorada)
====================================================================

📱 INFORMACIÓN DE LA APLICACIÓN:
- Nombre: EDF Catálogo de Tablas (Mejorado)
- Versión: 1.0.1
- Tipo: Aplicación nativa de macOS
- Desarrollador: EDF Sistemas
- Mejoras: Mejor manejo de cookies y sesiones

🚀 INSTALACIÓN:
1. Arrastrar "EDF_CatalogoDeTablas_Improved.app" a la carpeta "Aplicaciones"
2. Ejecutar desde Launchpad o Spotlight
3. Leer "MANUAL_APLICACION_NATIVA.md" para más información

📋 REQUISITOS:
- macOS 10.15 (Catalina) o superior
- 4GB RAM mínimo (8GB recomendado)
- 1GB espacio libre en disco

🔧 CARACTERÍSTICAS MEJORADAS:
- Aplicación nativa sin dependencia de navegador
- Mejor manejo de cookies y sesiones
- Configuración optimizada de pywebview
- Gestión de catálogos de productos
- Integración con Amazon S3 para imágenes
- Base de datos MongoDB
- Sistema de usuarios y autenticación

🆕 MEJORAS EN ESTA VERSIÓN:
- Configuración mejorada de pywebview
- Mejor manejo de cookies de sesión
- Configuración de seguridad de red optimizada
- Interfaz más estable y confiable
- Mejor experiencia de usuario

📞 SOPORTE:
- Contactar al administrador del sistema
- Revisar el manual para solución de problemas

© 2025 EDF Sistemas - Todos los derechos reservados
EOF

# Crear DMG
echo "💾 Creando DMG: $DMG_NAME"
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"

# Verificar que el DMG se creó correctamente
if [ -f "$DMG_NAME" ]; then
    echo "✅ DMG creado exitosamente: $DMG_NAME"
    
    # Mostrar información del DMG
    DMG_SIZE_BYTES=$(stat -f%z "$DMG_NAME")
    DMG_SIZE_MB=$((DMG_SIZE_BYTES / 1024 / 1024))
    echo "📊 Tamaño del DMG: ${DMG_SIZE_MB} MB"
    
    # Mover DMG a directorio dist
    mv "$DMG_NAME" "dist/"
    echo "📁 DMG movido a: dist/$DMG_NAME"
    
else
    echo "❌ Error: No se pudo crear el DMG"
    exit 1
fi

# Limpiar directorio temporal
echo "🧹 Limpiando archivos temporales..."
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 ¡DMG mejorado creado exitosamente!"
echo "================================================================"
echo "📁 Ubicación: dist/$DMG_NAME"
echo "📱 Aplicación: EDF_CatalogoDeTablas_Improved.app"
echo "📖 Manual: MANUAL_APLICACION_NATIVA.md"
echo "🔗 Enlace: Aplicaciones (para instalación fácil)"
echo ""
echo "🚀 Para distribuir:"
echo "   1. Compartir el archivo: dist/$DMG_NAME"
echo "   2. Los usuarios pueden montar el DMG"
echo "   3. Arrastrar la app a Aplicaciones"
echo "   4. Ejecutar desde Launchpad"
echo ""
echo "🆕 MEJORAS INCLUIDAS:"
echo "   - Mejor manejo de cookies y sesiones"
echo "   - Configuración optimizada de pywebview"
echo "   - Interfaz más estable"
echo "   - Mejor experiencia de usuario"
echo ""
echo "✅ ¡Listo para distribución!"
