#!/bin/bash
# Script para supervisar y gestionar Gunicorn desde la interfaz web
# Versión: 1.0 (18/05/2025)

# Variables de entorno
APP_DIR="$(dirname "$0")/../.."  # Directorio raíz del proyecto
LOG_DIR="$APP_DIR/logs"
GUNICORN_PID_FILE="$LOG_DIR/gunicorn.pid"
GUNICORN_CONFIG="$APP_DIR/gunicorn_config.py"
WSGI_APP="$APP_DIR/wsgi.py"
VENV="$APP_DIR/.venv"
SERVICE_NAME="edefrutos2025"

# Función para logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Verificar estado del servicio Gunicorn
check_service_status() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ El servicio $SERVICE_NAME está activo"
        return 0
    else
        echo "❌ El servicio $SERVICE_NAME NO está activo"
        return 1
    fi
}

# Verificar si el proceso Gunicorn está ejecutándose
check_process() {
    if pgrep -f "gunicorn.*$APP_DIR" > /dev/null; then
        echo "✅ Proceso Gunicorn encontrado"
        return 0
    else
        echo "❌ Proceso Gunicorn NO encontrado"
        return 1
    fi
}

# Verificar el archivo PID
check_pid_file() {
    if [ -f "$GUNICORN_PID_FILE" ]; then
        PID=$(cat "$GUNICORN_PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Archivo PID válido: $PID"
            return 0
        else
            echo "❌ Archivo PID existe pero el proceso no: $PID"
            return 1
        fi
    else
        echo "❌ Archivo PID no encontrado"
        return 1
    fi
}

# Verificar puertos
check_ports() {
    if netstat -tlpn 2>/dev/null | grep -q ":8002"; then
        echo "✅ Puerto 8002 en uso (esperado para Gunicorn)"
        return 0
    else
        echo "❌ Puerto 8002 NO está en uso"
        return 1
    fi
}

# Verificar logs
check_logs() {
    GUNICORN_ERROR_LOG="$LOG_DIR/gunicorn_error.log"
    GUNICORN_ACCESS_LOG="$LOG_DIR/gunicorn_access.log"
    
    if [ -f "$GUNICORN_ERROR_LOG" ]; then
        echo "✅ Log de errores existe"
        echo "Últimas 5 líneas del log de errores:"
        tail -n 5 "$GUNICORN_ERROR_LOG"
    else
        echo "❌ Log de errores NO existe"
    fi
    
    if [ -f "$GUNICORN_ACCESS_LOG" ]; then
        echo "✅ Log de acceso existe"
        echo "Últimas 5 líneas del log de acceso:"
        tail -n 5 "$GUNICORN_ACCESS_LOG"
    else
        echo "❌ Log de acceso NO existe"
    fi
}

# Verificar permisos
check_permissions() {
    if [ -w "$LOG_DIR" ]; then
        echo "✅ Permisos de escritura en directorio de logs"
    else
        echo "❌ NO hay permisos de escritura en directorio de logs"
    fi
    
    if [ -x "$VENV/bin/gunicorn" ]; then
        echo "✅ Gunicorn es ejecutable"
    else
        echo "❌ Gunicorn NO es ejecutable"
    fi
}

# Mostrar información del sistema
show_system_info() {
    echo "Información del sistema:"
    echo "- Hostname: $(hostname)"
    echo "- Usuario actual: $(whoami)"
    echo "- Tiempo de actividad: $(uptime)"
    echo "- Uso de CPU: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
    echo "- Uso de memoria: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')"
    echo "- Espacio en disco: $(df -h / | awk 'NR==2{print $5}')"
}

# Ejecutar diagnóstico completo
run_diagnostics() {
    echo "======================= DIAGNÓSTICO DE GUNICORN ======================="
    echo "Fecha y hora: $(date)"
    echo ""
    
    echo "1. Estado del servicio:"
    check_service_status
    echo ""
    
    echo "2. Proceso Gunicorn:"
    check_process
    echo ""
    
    echo "3. Archivo PID:"
    check_pid_file
    echo ""
    
    echo "4. Puertos en uso:"
    check_ports
    echo ""
    
    echo "5. Logs:"
    check_logs
    echo ""
    
    echo "6. Permisos:"
    check_permissions
    echo ""
    
    echo "7. Información del sistema:"
    show_system_info
    echo ""
    
    echo "======================= FIN DEL DIAGNÓSTICO ======================="
}

# Función principal
main() {
    case "$1" in
        status)
            check_service_status
            ;;
        diagnose)
            run_diagnostics
            ;;
        *)
            run_diagnostics
            ;;
    esac
}

# Ejecutar función principal
main "$@"
