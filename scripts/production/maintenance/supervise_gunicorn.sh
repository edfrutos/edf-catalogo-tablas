#!/bin/bash

# Variables de entorno
APP_DIR="/var/www/vhosts/edefrutos2025.xyz/httpdocs"
LOG_DIR="$APP_DIR/logs"
GUNICORN_PID_FILE="$LOG_DIR/gunicorn.pid"
SUPERVISOR_PID_FILE="$LOG_DIR/supervisor.pid"
MAX_RETRIES=5
RETRY_INTERVAL=10
USER="www-data"
GROUP="www-data"

# Registrar PID del supervisor
echo $$ > "$SUPERVISOR_PID_FILE"

# Verificar si se está ejecutando como root
if [ "$(id -u)" != "0" ]; then
    echo "Este script debe ejecutarse como root"
    exit 1
fi

# Asegurar permisos correctos
chown -R $USER:$GROUP $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $LOG_DIR

# Función para logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/supervisor.log"
    echo "$1"
}

# Función para verificar si Gunicorn está ejecutándose
check_gunicorn() {
    if [ -f "$GUNICORN_PID_FILE" ]; then
        if kill -0 $(cat "$GUNICORN_PID_FILE") 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Función para iniciar Gunicorn
start_gunicorn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando Gunicorn..." >> "$LOG_DIR/supervisor.log"
    $APP_DIR/start_gunicorn.sh >> "$LOG_DIR/supervisor.log" 2>&1 &
    sleep 5
}

# Función para detener Gunicorn
stop_gunicorn() {
    if [ -f "$GUNICORN_PID_FILE" ]; then
        pid=$(cat "$GUNICORN_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            log_message "Deteniendo Gunicorn (PID: $pid)"
            sudo -u $USER kill -TERM $pid
            sleep 5
            if kill -0 $pid 2>/dev/null; then
                log_message "Forzando detención de Gunicorn"
                sudo -u $USER kill -9 $pid
            fi
        fi
    fi
    sudo -u $USER pkill -f "gunicorn"
    sleep 2
}

# Bucle principal
while true; do
    if ! check_gunicorn; then
        log_message "Gunicorn no está ejecutándose. Reiniciando..."
        start_gunicorn
        
        # Verificar si el reinicio fue exitoso
        retries=0
        while ! check_gunicorn && [ $retries -lt $MAX_RETRIES ]; do
            log_message "Intento $((retries + 1)) de $MAX_RETRIES"
            sleep $RETRY_INTERVAL
            ((retries++))
        done
        
        if [ $retries -eq $MAX_RETRIES ]; then
            log_message "ERROR: No se pudo reiniciar Gunicorn después de $MAX_RETRIES intentos"
        else
            log_message "Gunicorn reiniciado exitosamente"
        fi
    fi
    
    sleep 10
done