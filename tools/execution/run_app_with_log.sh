#!/bin/bash
# Script avanzado para ejecutar la aplicación con logging
# Uso: ./run_app_with_log.sh

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Crear directorio de logs si no existe
mkdir -p logs

# Función para logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/app_startup.log
}

log_message "=== Iniciando aplicación ==="

# Verificaciones
if [ ! -d "venv310" ]; then
    log_message "ERROR: No se encontró el directorio venv310"
    exit 1
fi

if [ ! -f "venv310/bin/activate" ]; then
    log_message "ERROR: No se encontró venv310/bin/activate"
    exit 1
fi

if [ ! -f "main_app.py" ]; then
    log_message "ERROR: No se encontró main_app.py"
    exit 1
fi

# Activar entorno virtual
log_message "Activando entorno virtual..."
source venv310/bin/activate

# Verificar que Python está disponible
if ! command -v python &> /dev/null; then
    log_message "ERROR: Python no está disponible en el entorno virtual"
    exit 1
fi

# Mostrar información del entorno
log_message "Python version: $(python --version)"
log_message "Python path: $(which python)"

# Ejecutar la aplicación con logging
log_message "Ejecutando main_app.py..."
echo "=== Iniciando aplicación $(date) ===" >> logs/consola_terminal_python.log

# Usar tu sistema de logging existente
./logcmdpy.sh python main_app.py

log_message "=== Aplicación finalizada ==="
