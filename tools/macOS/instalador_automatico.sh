#!/bin/bash

# 🍎 Instalador Automático para EDF CatálogoDeTablas
# ===================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

# Función para mostrar el banner
show_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    EDF CATÁLOGODETABLAS                      ║"
    echo "║                     Instalador v1.0.0                        ║"
    echo "║                                                              ║"
    echo "║              Aplicación de Catalogación de Tablas            ║"
    echo "║                        para macOS                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para verificar requisitos del sistema
check_system_requirements() {
    print_header "Verificando requisitos del sistema..."
    
    # Verificar versión de macOS
    MACOS_VERSION=$(sw_vers -productVersion)
    print_info "Versión de macOS detectada: $MACOS_VERSION"
    
    # Verificar si es compatible (10.13 o superior)
    if [[ $(echo "$MACOS_VERSION" | cut -d. -f2) -ge 13 ]]; then
        print_status "Versión de macOS compatible"
    else
        print_error "Se requiere macOS 10.13 o superior"
        print_info "Tu versión actual: $MACOS_VERSION"
        exit 1
    fi
    
    # Verificar arquitectura
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" || "$ARCH" == "x86_64" ]]; then
        print_status "Arquitectura compatible: $ARCH"
    else
        print_error "Arquitectura no compatible: $ARCH"
        exit 1
    fi
    
    # Verificar espacio en disco
    AVAILABLE_SPACE=$(df /Applications | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=500000  # 500MB en KB
    
    if [[ $AVAILABLE_SPACE -gt $REQUIRED_SPACE ]]; then
        print_status "Espacio en disco suficiente"
    else
        print_warning "Espacio en disco limitado"
        print_info "Espacio disponible: $((AVAILABLE_SPACE / 1024))MB"
        print_info "Espacio requerido: $((REQUIRED_SPACE / 1024))MB"
    fi
    
    # Verificar conexión a internet
    if ping -c 1 google.com &> /dev/null; then
        print_status "Conexión a internet disponible"
    else
        print_warning "No se detectó conexión a internet"
        print_info "Algunas funcionalidades pueden no estar disponibles"
    fi
}

# Función para instalar la aplicación
install_application() {
    print_header "Instalando EDF CatálogoDeTablas..."
    
    # Obtener la ruta del script actual
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    APP_SOURCE="$SCRIPT_DIR/EDF_CatalogoDeTablas.app"
    APP_DEST="/Applications/EDF_CatalogoDeTablas.app"
    
    # Verificar que la aplicación existe en el directorio actual
    if [ ! -d "$APP_SOURCE" ]; then
        print_error "No se encontró la aplicación en el directorio actual"
        print_info "Asegúrate de ejecutar este script desde el DMG montado"
        exit 1
    fi
    
    # Verificar si ya existe una instalación previa
    if [ -d "$APP_DEST" ]; then
        print_warning "Se detectó una instalación previa"
        read -p "¿Deseas sobrescribir la instalación existente? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Instalación cancelada"
            exit 0
        fi
        
        print_info "Eliminando instalación previa..."
        rm -rf "$APP_DEST"
    fi
    
    # Copiar la aplicación
    print_info "Copiando aplicación a /Applications..."
    cp -R "$APP_SOURCE" "$APP_DEST"
    
    # Establecer permisos correctos
    print_info "Configurando permisos..."
    chmod +x "$APP_DEST/Contents/MacOS/EDF_CatalogoDeTablas"
    chown -R $(whoami):staff "$APP_DEST"
    
    # Limpiar atributos extendidos
    print_info "Limpiando atributos extendidos..."
    xattr -cr "$APP_DEST" 2>/dev/null || true
    
    print_status "Aplicación instalada correctamente"
}

# Función para configurar la aplicación
configure_application() {
    print_header "Configurando la aplicación..."
    
    # Crear directorio de logs si no existe
    LOGS_DIR="$HOME/Library/Logs/EDF_CatalogoDeTablas"
    if [ ! -d "$LOGS_DIR" ]; then
        print_info "Creando directorio de logs..."
        mkdir -p "$LOGS_DIR"
    fi
    
    # Crear directorio de configuración
    CONFIG_DIR="$HOME/Library/Application Support/EDF_CatalogoDeTablas"
    if [ ! -d "$CONFIG_DIR" ]; then
        print_info "Creando directorio de configuración..."
        mkdir -p "$CONFIG_DIR"
    fi
    
    print_status "Configuración completada"
}

# Función para crear enlaces en el Dock
setup_dock() {
    print_header "Configurando acceso rápido..."
    
    read -p "¿Deseas agregar la aplicación al Dock? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Agregando al Dock..."
        defaults write com.apple.dock persistent-apps -array-add '{"tile-type"="file-tile";"tile-data"={"file-data"={"_CFURLString"="file:///Applications/EDF_CatalogoDeTablas.app";"_CFURLStringType"="15";};};}'
        killall Dock
        print_status "Aplicación agregada al Dock"
    else
        print_info "Omitiendo configuración del Dock"
    fi
}

# Función para mostrar información post-instalación
show_post_install_info() {
    print_header "Instalación Completada Exitosamente!"
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ¡INSTALACIÓN EXITOSA!                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_info "La aplicación ha sido instalada en:"
    echo "   📁 /Applications/EDF_CatalogoDeTablas.app"
    
    print_info "Para iniciar la aplicación:"
    echo "   1. 🖱️  Desde Finder: Ve a Aplicaciones y haz doble clic"
    echo "   2. ⌨️  Desde Terminal: open /Applications/EDF_CatalogoDeTablas.app"
    echo "   3. 🚀 Desde Spotlight: Cmd+Espacio y escribe 'EDF'"
    
    print_info "Credenciales iniciales:"
    echo "   👤 Usuario: edefrutos"
    echo "   🔑 Contraseña: Contacta al administrador"
    
    print_warning "Primera ejecución:"
    echo "   ⚠️  macOS puede mostrar una advertencia de seguridad"
    echo "   ✅ Haz clic en 'Abrir' para permitir la ejecución"
    
    print_info "Soporte técnico:"
    echo "   📧 Email: soporte@edefrutos2025.xyz"
    echo "   🌐 Web: https://edefrutos2025.xyz"
    
    echo ""
    print_status "¡La aplicación está lista para usar!"
}

# Función principal
main() {
    show_banner
    
    print_info "Este instalador configurará EDF CatálogoDeTablas en tu Mac"
    echo ""
    
    # Verificar que se ejecute como usuario normal
    if [[ $EUID -eq 0 ]]; then
        print_error "No ejecutes este script como root"
        print_info "Ejecuta el script como usuario normal"
        exit 1
    fi
    
    # Verificar requisitos
    check_system_requirements
    
    echo ""
    read -p "¿Deseas continuar con la instalación? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Instalación cancelada"
        exit 0
    fi
    
    echo ""
    
    # Instalar aplicación
    install_application
    
    # Configurar aplicación
    configure_application
    
    # Configurar Dock
    setup_dock
    
    echo ""
    
    # Mostrar información post-instalación
    show_post_install_info
    
    echo ""
    read -p "Presiona Enter para abrir la aplicación ahora..."
    
    # Abrir la aplicación
    open "/Applications/EDF_CatalogoDeTablas.app"
    
    print_status "¡Instalación completada! La aplicación se está abriendo..."
}

# Ejecutar función principal
main "$@"
