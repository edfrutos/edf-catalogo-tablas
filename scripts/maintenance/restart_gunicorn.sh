#!/bin/bash
# Script mejorado para reiniciar Gunicorn con manejo de señales y opciones de configuración
# Versión: 2.0.0

# Configuración por defecto
DEFAULT_WORKERS=$(( $(nproc) * 2 + 1 ))
DEFAULT_PORT=8000
DEFAULT_TIMEOUT=300
DEFAULT_LOG_LEVEL="info"
DEFAULT_BIND="0.0.0.0"
DEFAULT_MAX_REQUESTS=1000
DEFAULT_WORKER_CLASS="gthread"
DEFAULT_THREADS=2
DEFAULT_CONFIG_FILE="/etc/edf_catalogotablas/gunicorn.conf"
APP_MODULE="app:create_app()"

# Constantes
SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOCK_FILE="/var/run/${SCRIPT_NAME%.*}.pid"
LOG_FILE="/var/log/edf_catalogotablas/gunicorn_restart.log"

# Colores para el logging
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Variables globales
declare -r DEPENDENCIES=("gunicorn" "lsof" "ps" "netstat" "pgrep")
declare -a CHILD_PIDS=()

# Cargar configuración desde archivo si existe
load_config() {
    local config_file="${1:-$DEFAULT_CONFIG_FILE}"
    if [[ -f "$config_file" ]]; then
        log "DEBUG" "Cargando configuración desde $config_file"
        # shellcheck source=/dev/null
        source "$config_file"
    fi
}

# Función para mostrar ayuda
display_help() {
    echo -e "${BLUE}Uso:${NC} $0 [opciones]"
    echo -e "\n${BLUE}Opciones:${NC}"
    echo -e "  -h, --help             Mostrar este mensaje de ayuda"
    echo -e "  -w, --workers N        Número de workers (por defecto: $DEFAULT_WORKERS)"
    echo -e "  -p, --port N           Puerto para Gunicorn (por defecto: $DEFAULT_PORT)"
    echo -e "  -t, --timeout N        Tiempo de espera en segundos (por defecto: $DEFAULT_TIMEOUT)"
    echo -e "  -l, --log-level LEVEL  Nivel de logging (debug, info, warning, error, critical)"
    echo -e "  -e, --env ENV          Entorno (production/development, por defecto: production)"
    echo -e "  -c, --config FILE      Archivo de configuración (por defecto: $DEFAULT_CONFIG_FILE)"
    echo -e "  --reload               Recargar automáticamente en desarrollo"
    echo -e "  --max-requests N       Máximo número de peticiones por worker (por defecto: $DEFAULT_MAX_REQUESTS)"
    echo -e "  --worker-class CLASS   Clase de worker a utilizar (por defecto: $DEFAULT_WORKER_CLASS)"
    echo -e "  --threads N            Número de hilos por worker (por defecto: $DEFAULT_THREADS)"
    echo -e "\n${BLUE}Ejemplos:${NC}"
    echo -e "  $0 --env production --workers 4 --port 8000"
    echo -e "  $0 --config /ruta/a/mi_configuracion.conf"
    exit 0
}

# Función para loguear mensajes
log() {
    local level="${1}"
    local message="${2}"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_msg="[${timestamp}] ${level}: ${message}"
    
    # Colorear la salida según el nivel
    case "${level}" in
        "DEBUG")
            echo -e "${BLUE}${log_msg}${NC}"
            ;;
        "INFO")
            echo -e "${GREEN}${log_msg}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}${log_msg}${NC}" >&2
            ;;
        "ERROR" | "CRITICAL")
            echo -e "${RED}${log_msg}${NC}" >&2
            ;;
        *)
            echo "${log_msg}"
            ;;
    esac
    
    # Registrar en archivo de log
    echo "${timestamp} [${level}] [${SCRIPT_NAME}] ${message}" >> "${LOG_FILE}"
}

# Función para salir del script
die() {
    local message="${1:-'Error inesperado'}"
    local code=${2:-1}
    log "ERROR" "${message}"
    cleanup
    exit "${code}"
}

# Función para limpiar recursos
cleanup() {
    log "INFO" "Limpiando recursos..."
    
    # Eliminar archivo de bloqueo
    if [[ -f "${LOCK_FILE}" ]]; then
        rm -f "${LOCK_FILE}" || log "WARNING" "No se pudo eliminar el archivo de bloqueo: ${LOCK_FILE}"
    fi
    
    # Detener procesos hijos
    for pid in "${CHILD_PIDS[@]}"; do
        if kill -0 "${pid}" 2>/dev/null; then
            log "DEBUG" "Deteniendo proceso hijo con PID: ${pid}"
            kill -TERM "${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null
        fi
    done
}

# Función para configurar el manejo de señales
setup_signal_handlers() {
    trap 'cleanup; exit 0' INT TERM
    trap 'die "Error en la línea $LINENO"' ERR
}

# Función para verificar dependencias
check_dependencies() {
    local missing_deps=()
    
    for dep in "${DEPENDENCIES[@]}"; do
        if ! command -v "${dep}" &> /dev/null; then
            missing_deps+=("${dep}")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        die "Faltan dependencias requeridas: ${missing_deps[*]}. Por favor, instálalas y vuelve a intentarlo."
    fi
}

# Función para verificar si ya hay una instancia en ejecución
check_running_instance() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local pid
        pid=$(cat "${LOCK_FILE}")
        if ps -p "${pid}" > /dev/null 2>&1; then
            die "Ya hay una instancia de ${SCRIPT_NAME} en ejecución con PID: ${pid}"
        else
            log "WARNING" "Se encontró un archivo de bloqueo obsoleto. Eliminando..."
            rm -f "${LOCK_FILE}" || die "No se pudo eliminar el archivo de bloqueo obsoleto"
        fi
    fi
    
    # Crear archivo de bloqueo
    echo "$$" > "${LOCK_FILE}" || die "No se pudo crear el archivo de bloqueo"
}

# Función para verificar si un puerto está en uso
is_port_in_use() {
    local port="$1"
    if lsof -i ":${port}" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Función para encontrar el proceso Gunicorn
get_gunicorn_pid() {
    pgrep -f "gunicorn.*:${PORT}" || echo ""
}

# Función para detener Gunicorn de manera segura
stop_gunicorn() {
    local pid
    pid=$(get_gunicorn_pid)
    
    if [[ -n "${pid}" ]]; then
        log "INFO" "Deteniendo Gunicorn (PID: ${pid})..."
        kill -TERM "${pid}" 2>/dev/null || true
        
        # Esperar hasta que el proceso termine o se agote el tiempo
        local timeout=30
        while kill -0 "${pid}" 2>/dev/null && [[ ${timeout} -gt 0 ]]; do
            sleep 1
            ((timeout--))
        done
        
        # Si el proceso sigue en ejecución, forzar terminación
        if kill -0 "${pid}" 2>/dev/null; then
            log "WARNING" "Forzando terminación de Gunicorn (PID: ${pid})..."
            kill -9 "${pid}" 2>/dev/null || true
        fi
        
        log "INFO" "Gunicorn detenido correctamente"
    else
        log "INFO" "No se encontró ninguna instancia de Gunicorn en ejecución"
    fi
}

# Función para iniciar Gunicorn
start_gunicorn() {
    local gunicorn_cmd=(
        "gunicorn"
        "${APP_MODULE}"
        "--workers=${WORKERS}"
        "--bind=${DEFAULT_BIND}:${PORT}"
        "--timeout=${TIMEOUT}"
        "--log-level=${LOG_LEVEL}"
        "--worker-class=${WORKER_CLASS}"
        "--threads=${THREADS}"
        "--max-requests=${MAX_REQUESTS}"
        "--max-requests-jitter=100"
        "--access-logfile=-"
        "--error-logfile=-"
        "--capture-output"
        "--enable-stdio-inheritance"
    )
    
    if [[ "${ENVIRONMENT}" == "development" ]]; then
        gunicorn_cmd+=( "--reload" )
    fi
    
    log "INFO" "Iniciando Gunicorn en el puerto ${PORT} con ${WORKERS} workers..."
    log "DEBUG" "Comando: ${gunicorn_cmd[*]}"
    
    # Ejecutar en segundo plano y capturar el PID
    "${gunicorn_cmd[@]}" & 
    local gunicorn_pid=$!
    CHILD_PIDS+=("${gunicorn_pid}")
    
    # Esperar a que el servidor esté listo
    local timeout=30
    while ! lsof -i ":${PORT}" > /dev/null 2>&1 && [[ ${timeout} -gt 0 ]]; do
        sleep 1
        ((timeout--))
    done
    
    if [[ ${timeout} -eq 0 ]]; then
        die "Tiempo de espera agotado al iniciar Gunicorn"
    fi
    
    log "INFO" "Gunicorn iniciado correctamente con PID: ${gunicorn_pid}"
}

# Función principal
main() {
    log "INFO" "=== Iniciando ${SCRIPT_NAME} ==="
    log "INFO" "Directorio de trabajo: ${SCRIPT_DIR}"
    
    # Procesar argumentos
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                display_help
                ;;
            -w|--workers)
                WORKERS="$2"
                shift 2
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -l|--log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                load_config "$2"
                shift 2
                ;;
            --reload)
                RELOAD="--reload"
                shift
                ;;
            --max-requests)
                MAX_REQUESTS="$2"
                shift 2
                ;;
            --worker-class)
                WORKER_CLASS="$2"
                shift 2
                ;;
            --threads)
                THREADS="$2"
                shift 2
                ;;
            *)
                log "ERROR" "Opción desconocida: $1"
                display_help
                ;;
        esac
    done
    
    # Establecer valores por defecto si no están definidos
    WORKERS=${WORKERS:-$DEFAULT_WORKERS}
    PORT=${PORT:-$DEFAULT_PORT}
    TIMEOUT=${TIMEOUT:-$DEFAULT_TIMEOUT}
    LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
    ENVIRONMENT=${ENVIRONMENT:-"production"}
    WORKER_CLASS=${WORKER_CLASS:-$DEFAULT_WORKER_CLASS}
    THREADS=${THREADS:-$DEFAULT_THREADS}
    MAX_REQUESTS=${MAX_REQUESTS:-$DEFAULT_MAX_REQUESTS}
    
    # Verificar dependencias
    check_dependencies
    
    # Configurar manejo de señales
    setup_signal_handlers
    
    # Verificar instancia en ejecución
    check_running_instance
    
    # Verificar si el puerto está en uso
    if is_port_in_use "${PORT}"; then
        log "WARNING" "El puerto ${PORT} está en uso. Intentando detener el proceso..."
        stop_gunicorn
    fi
    
    # Iniciar Gunicorn
    start_gunicorn
    
    log "INFO" "=== ${SCRIPT_NAME} completado exitosamente ==="
    cleanup
    exit 0
}

# Ejecutar función principal
main "$@"