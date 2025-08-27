#!/bin/bash

# Script de Lanzamiento - Interfaz Web de Verificación de Funcionalidad
# EDF_CatalogoDeTablas - Sistema de Verificación Automática

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  VERIFICADOR DE FUNCIONALIDAD${NC}"
    echo -e "${BLUE}  EDF_CatalogoDeTablas${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Función para verificar dependencias
check_dependencies() {
    print_message "Verificando dependencias..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 no está instalado"
        exit 1
    fi
    
    # Verificar Flask
    if ! python3 -c "import flask" &> /dev/null; then
        print_error "Flask no está instalado"
        exit 1
    fi
    
    print_message "✅ Dependencias verificadas"
}

# Función para verificar el entorno
check_environment() {
    print_message "Verificando entorno..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "app/__init__.py" ]; then
        print_error "No se encontró app/__init__.py. Ejecuta desde el directorio raíz del proyecto."
        exit 1
    fi
    
    # Verificar que existe el script de verificación
    if [ ! -f "tools/app_functionality_checker.py" ]; then
        print_error "No se encontró tools/app_functionality_checker.py"
        exit 1
    fi
    
    # Crear directorio de logs si no existe
    mkdir -p logs
    
    print_message "✅ Entorno verificado"
}

# Función para ejecutar verificación rápida
run_quick_check() {
    print_message "Ejecutando verificación rápida..."
    
    if python3 tools/app_functionality_checker.py; then
        print_message "✅ Verificación completada"
    else
        print_error "❌ Error en la verificación"
        exit 1
    fi
}

# Función para lanzar interfaz web
launch_web_interface() {
    print_message "Lanzando interfaz web..."
    
    # Verificar si el puerto 5001 está disponible
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Puerto 5001 ya está en uso. Intentando puerto 5002..."
        PORT=5002
    else
        PORT=5001
    fi
    
    print_message "🌐 Interfaz web disponible en: http://localhost:$PORT"
    print_message "📱 Presiona Ctrl+C para detener el servidor"
    
    # Lanzar la interfaz web
    python3 tools/functionality_check_web_interface.py
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  check     - Ejecutar verificación rápida desde línea de comandos"
    echo "  web       - Lanzar interfaz web (por defecto)"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 check    # Verificación rápida"
    echo "  $0 web      # Interfaz web"
    echo "  $0          # Interfaz web (por defecto)"
}

# Función principal
main() {
    print_header
    
    # Verificar argumentos
    case "${1:-web}" in
        "check")
            check_dependencies
            check_environment
            run_quick_check
            ;;
        "web")
            check_dependencies
            check_environment
            launch_web_interface
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
