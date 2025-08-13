#!/bin/bash

# 🍎 Script para crear DMG de EDF CatálogoDeTablas para macOS
# =============================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🍎 $1${NC}"
}

# Verificar que estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "Este script solo funciona en macOS"
    exit 1
fi

print_header "Iniciando creación de DMG para EDF CatálogoDeTablas"

# Verificar que la aplicación existe
if [ ! -d "dist/EDF_CatalogoDeTablas.app" ]; then
    print_error "La aplicación no existe. Ejecuta primero: ./build_macos_app.sh"
    exit 1
fi

# Crear directorio temporal para el DMG
TEMP_DIR="temp_dmg"
DMG_NAME="EDF_CatalogoDeTablas_v1.0.0"
FINAL_DMG="${DMG_NAME}.dmg"

print_info "Limpiando directorio temporal..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

print_info "Copiando aplicación al directorio temporal..."
cp -R "dist/EDF_CatalogoDeTablas.app" "$TEMP_DIR/"

print_info "Creando enlaces simbólicos..."
# Crear enlace a Aplicaciones
ln -s /Applications "$TEMP_DIR/Aplicaciones"

print_info "Copiando documentación..."
# Copiar README
cp "README_MACOS.md" "$TEMP_DIR/README.md"

# Copiar instalador automático
cp "instalador_automatico.sh" "$TEMP_DIR/INSTALAR.sh"
chmod +x "$TEMP_DIR/INSTALAR.sh"

# Crear archivo de instalación
cat > "$TEMP_DIR/INSTALAR.txt" << 'EOF'
🍎 INSTALACIÓN DE EDF CATÁLOGODETABLAS
=====================================

MÉTODO 1 - INSTALACIÓN AUTOMÁTICA (RECOMENDADO):
1. Arrastra "EDF_CatalogoDeTablas.app" a la carpeta "Aplicaciones"
2. Ve a Aplicaciones y haz doble clic en "EDF_CatalogoDeTablas"
3. Si macOS muestra una advertencia, haz clic en "Abrir"

MÉTODO 2 - INSTALACIÓN MANUAL:
1. Abre Terminal
2. Ejecuta: cp -R "EDF_CatalogoDeTablas.app" /Applications/
3. Ve a Aplicaciones y ejecuta la aplicación

CONFIGURACIÓN INICIAL:
- Usuario: edefrutos
- Contraseña: Contacta al administrador
- Requiere conexión a internet para funcionar

Para más información, consulta README.md
EOF

# Crear archivo de requisitos del sistema
cat > "$TEMP_DIR/REQUISITOS.txt" << 'EOF'
🖥️ REQUISITOS DEL SISTEMA
=========================

SISTEMA OPERATIVO:
- macOS 10.13 (High Sierra) o superior
- Compatible con Intel x64 y Apple Silicon (ARM64)

HARDWARE:
- Memoria RAM: Mínimo 4GB, recomendado 8GB
- Espacio en disco: 500MB para la aplicación
- Conexión a internet requerida

FUNCIONALIDADES:
✅ Catalogación de tablas
✅ Gestión de usuarios
✅ Backup a Google Drive
✅ Sincronización con Amazon S3
✅ Panel de administración
✅ Herramientas de mantenimiento
✅ Exportación a CSV/Excel/PDF
✅ Sistema de logs y auditoría

SOPORTE:
- Email: soporte@edefrutos2025.xyz
- Web: https://edefrutos2025.xyz
EOF

# Crear archivo de cambios de versión
cat > "$TEMP_DIR/CAMBIOS_v1.0.0.txt" << 'EOF'
🗓️ CAMBIOS EN VERSIÓN 1.0.0
===========================

NUEVAS FUNCIONALIDADES:
✅ Aplicación de escritorio nativa para macOS
✅ Interfaz completa de catalogación de tablas
✅ Sistema de autenticación con roles
✅ Panel de administración completo
✅ Integración con Google Drive para backups
✅ Sincronización con Amazon S3 para imágenes
✅ Herramientas de mantenimiento y diagnóstico
✅ Sistema de logging unificado
✅ Exportación a múltiples formatos
✅ Gestión de usuarios y permisos

MEJORAS TÉCNICAS:
✅ Optimización para macOS 10.13+
✅ Soporte para Apple Silicon (ARM64)
✅ Interfaz nativa con PyWebView
✅ Empaquetado optimizado con PyInstaller
✅ Gestión automática de dependencias
✅ Configuración automática de directorios

CORRECCIONES:
✅ Arranque desde Finder funcionando
✅ Rutas de archivos corregidas
✅ Credenciales de Google Drive incluidas
✅ Permisos de ejecución configurados
✅ Atributos extendidos limpiados

FECHA DE LANZAMIENTO: 13 de Agosto, 2025
EOF

# Crear archivo de licencia
cat > "$TEMP_DIR/LICENCIA.txt" << 'EOF'
📄 LICENCIA DE USO
==================

EDF CATÁLOGODETABLAS v1.0.0

PROPIEDAD INTELECTUAL:
Esta aplicación es propiedad de EDFrutos y está protegida 
por derechos de autor. Todos los derechos reservados.

TÉRMINOS DE USO:
1. Esta aplicación está destinada para uso interno de EDFrutos
2. No está permitida la redistribución sin autorización
3. No está permitida la ingeniería inversa
4. El uso comercial requiere licencia específica

CONTACTO PARA LICENCIAS:
- Email: licencias@edefrutos2025.xyz
- Web: https://edefrutos2025.xyz

SOPORTE TÉCNICO:
- Email: soporte@edefrutos2025.xyz
- Documentación: Disponible en el panel de administración

© 2025 EDFrutos. Todos los derechos reservados.
EOF

print_info "Configurando vista del DMG..."
# Crear archivo .DS_Store personalizado para la vista
cat > "$TEMP_DIR/.DS_Store" << 'EOF'
# Este archivo se generará automáticamente al abrir el DMG
EOF

print_info "Creando DMG..."
# Crear el DMG
hdiutil create -volname "EDF CatálogoDeTablas v1.0.0" -srcfolder "$TEMP_DIR" -ov -format UDZO "$FINAL_DMG"

print_info "Limpiando archivos temporales..."
rm -rf "$TEMP_DIR"

# Verificar que el DMG se creó correctamente
if [ -f "$FINAL_DMG" ]; then
    DMG_SIZE=$(du -h "$FINAL_DMG" | cut -f1)
    print_status "DMG creado exitosamente: $FINAL_DMG"
    print_info "Tamaño del DMG: $DMG_SIZE"
    
    print_header "Contenido del DMG:"
    echo "📁 EDF_CatalogoDeTablas.app (Aplicación principal)"
    echo "📁 Aplicaciones (Enlace simbólico)"
    echo "📄 README.md (Documentación completa)"
    echo "🚀 INSTALAR.sh (Instalador automático)"
    echo "📄 INSTALAR.txt (Instrucciones de instalación)"
    echo "📄 REQUISITOS.txt (Requisitos del sistema)"
    echo "📄 CAMBIOS_v1.0.0.txt (Cambios de versión)"
    echo "📄 LICENCIA.txt (Términos de licencia)"
    
    print_header "Próximos pasos:"
    echo "1. 📦 El DMG está listo para distribución"
    echo "2. 🚀 Los usuarios pueden montar el DMG y arrastrar la app a Aplicaciones"
    echo "3. 📋 La documentación está incluida en el DMG"
    echo "4. 🔧 No se requieren instalaciones adicionales"
    
    print_status "¡DMG creado exitosamente!"
    print_info "Ubicación: $(pwd)/$FINAL_DMG"
    
else
    print_error "Error al crear el DMG"
    exit 1
fi

print_header "Proceso completado exitosamente! 🎉"
