#!/bin/bash

# =========================================
# INSTALADOR COMPLETO DE PYTHON 3.10.*
# Para Ubuntu/Debian Linux
# =========================================

set -e

echo "🐍 INSTALADOR DE PYTHON 3.10.* PARA LINUX"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[PASO $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para detectar distribución
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
        print_success "Detectado: $PRETTY_NAME"
    else
        print_error "No se pudo detectar la distribución"
        exit 1
    fi
}

# Función para Ubuntu/Debian
install_ubuntu_debian() {
    print_step "1" "Actualizando sistema..."
    sudo apt update

    print_step "2" "Instalando dependencias..."
    sudo apt install -y software-properties-common curl

    print_step "3" "Agregando PPA deadsnakes..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update

    print_step "4" "Instalando Python 3.10 y componentes..."
    sudo apt install -y \
        python3.10 \
        python3.10-dev \
        python3.10-venv \
        python3.10-distutils \
        python3.10-gdbm \
        python3.10-tk

    print_step "5" "Instalando pip para Python 3.10..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

    print_success "Python 3.10 instalado exitosamente"
}

# Función para CentOS/RHEL/Fedora
install_centos_rhel_fedora() {
    print_warning "Para CentOS/RHEL/Fedora, recomendamos usar pyenv o compilar desde fuente"
    
    print_step "1" "Instalando dependencias de desarrollo..."
    if command -v dnf &> /dev/null; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y \
            openssl-devel \
            bzip2-devel \
            libffi-devel \
            zlib-devel \
            readline-devel \
            sqlite-devel \
            wget \
            curl \
            llvm
    elif command -v yum &> /dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            openssl-devel \
            bzip2-devel \
            libffi-devel \
            zlib-devel \
            readline-devel \
            sqlite-devel \
            wget \
            curl \
            llvm
    fi

    print_step "2" "Instalando pyenv..."
    curl https://pyenv.run | bash
    
    print_warning "Después de reiniciar la terminal, ejecuta:"
    echo "export PATH=\"\$HOME/.pyenv/bin:\$PATH\""
    echo "eval \"\$(pyenv init --path)\""
    echo "eval \"\$(pyenv virtualenv-init -)\""
    echo "pyenv install 3.10.18"
    echo "pyenv global 3.10.18"
}

# Función para Arch Linux
install_arch() {
    print_step "1" "Actualizando sistema..."
    sudo pacman -Syu

    print_step "2" "Instalando Python 3.10 desde AUR..."
    if ! command -v yay &> /dev/null; then
        print_warning "Instalando yay (AUR helper)..."
        git clone https://aur.archlinux.org/yay.git
        cd yay
        makepkg -si
        cd ..
        rm -rf yay
    fi

    yay -S python310

    print_step "3" "Instalando pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

    print_success "Python 3.10 instalado exitosamente"
}

# Función para crear entorno virtual
create_venv() {
    local project_dir="$1"
    local venv_name="${2:-.venv310}"
    
    print_step "6" "Creando entorno virtual..."
    
    if [ -n "$project_dir" ] && [ -d "$project_dir" ]; then
        cd "$project_dir"
        print_success "Cambiando a directorio: $project_dir"
    fi
    
    python3.10 -m venv "$venv_name"
    print_success "Entorno virtual creado: $venv_name"
    
    print_step "7" "Activando entorno virtual y actualizando pip..."
    source "$venv_name/bin/activate"
    pip install --upgrade pip
    
    print_success "Entorno virtual configurado y listo"
    
    echo ""
    echo "Para activar el entorno virtual en el futuro:"
    echo "source $venv_name/bin/activate"
}

# Función de verificación
verify_installation() {
    print_step "8" "Verificando instalación..."
    
    local python_version=$(python3.10 --version 2>&1)
    local pip_version=$(python3.10 -m pip --version 2>&1)
    
    print_success "Python instalado: $python_version"
    print_success "Pip instalado: $pip_version"
    
    echo ""
    echo "🎯 COMANDOS ÚTILES:"
    echo "==================="
    echo "python3.10 --version          # Ver versión"
    echo "python3.10 -m pip --version   # Ver versión pip"
    echo "python3.10 -m venv mi_env     # Crear entorno virtual"
    echo "source mi_env/bin/activate    # Activar entorno"
    echo "deactivate                    # Desactivar entorno"
}

# Función principal
main() {
    echo ""
    detect_distro
    
    case $DISTRO in
        ubuntu|debian|pop|linuxmint)
            install_ubuntu_debian
            ;;
        centos|rhel|fedora|rocky|almalinux)
            install_centos_rhel_fedora
            return 0  # Salir aquí para CentOS/RHEL/Fedora
            ;;
        arch|manjaro)
            install_arch
            ;;
        *)
            print_error "Distribución no soportada: $DISTRO"
            echo ""
            echo "OPCIONES MANUALES:"
            echo "1. Usar pyenv: curl https://pyenv.run | bash"
            echo "2. Compilar desde fuente: https://www.python.org/downloads/source/"
            echo "3. Usar Docker: docker run -it python:3.10"
            exit 1
            ;;
    esac
    
    verify_installation
    
    # Preguntar si crear entorno virtual
    echo ""
    read -p "¿Crear entorno virtual? (y/N): " create_env
    if [[ $create_env =~ ^[Yy]$ ]]; then
        read -p "Directorio del proyecto (presiona Enter para directorio actual): " project_dir
        read -p "Nombre del entorno virtual (presiona Enter para .venv310): " venv_name
        create_venv "$project_dir" "$venv_name"
    fi
    
    echo ""
    print_success "¡Instalación completada exitosamente!"
    echo ""
    echo "🚀 PRÓXIMOS PASOS:"
    echo "=================="
    echo "1. Reiniciar la terminal si es necesario"
    echo "2. Crear un proyecto: mkdir mi_proyecto && cd mi_proyecto"
    echo "3. Crear entorno virtual: python3.10 -m venv .venv"
    echo "4. Activar entorno: source .venv/bin/activate"
    echo "5. Instalar dependencias: pip install -r requirements.txt"
}

# Mostrar ayuda
show_help() {
    echo "USO: $0 [OPCIONES]"
    echo ""
    echo "OPCIONES:"
    echo "  -h, --help     Mostrar esta ayuda"
    echo "  -v, --verify   Solo verificar instalación existente"
    echo ""
    echo "DISTRIBUCIONES SOPORTADAS:"
    echo "  ✅ Ubuntu 18.04+"
    echo "  ✅ Debian 9+"
    echo "  ✅ Linux Mint"
    echo "  ✅ Pop!_OS"
    echo "  ⚠️  CentOS/RHEL/Fedora (con pyenv)"
    echo "  ⚠️  Arch Linux (con AUR)"
}

# Verificar argumentos
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--verify)
        verify_installation
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Opción desconocida: $1"
        show_help
        exit 1
        ;;
esac