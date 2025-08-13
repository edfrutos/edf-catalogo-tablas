#!/bin/bash
# Script para ejecutar la aplicación como servicio en background
# Uso: ./run_app_service.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PIDFILE="$SCRIPT_DIR/app.pid"
LOGFILE="$SCRIPT_DIR/logs/app_service.log"

# Crear directorio de logs si no existe
mkdir -p logs

start_app() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "La aplicación ya está ejecutándose (PID: $(cat $PIDFILE))"
        return 1
    fi
    
    echo "Iniciando aplicación..."
    source venv310/bin/activate
    nohup python main_app.py > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "Aplicación iniciada (PID: $(cat $PIDFILE))"
}

stop_app() {
    if [ ! -f "$PIDFILE" ]; then
        echo "No se encontró archivo PID. La aplicación no parece estar ejecutándose."
        return 1
    fi
    
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Deteniendo aplicación (PID: $PID)..."
        kill "$PID"
        rm -f "$PIDFILE"
        echo "Aplicación detenida"
    else
        echo "El proceso $PID no existe. Limpiando archivo PID..."
        rm -f "$PIDFILE"
    fi
}

status_app() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "La aplicación está ejecutándose (PID: $(cat $PIDFILE))"
        return 0
    else
        echo "La aplicación no está ejecutándose"
        return 1
    fi
}

case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        sleep 2
        start_app
        ;;
    status)
        status_app
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        echo ""
        echo "  start   - Iniciar la aplicación en background"
        echo "  stop    - Detener la aplicación"
        echo "  restart - Reiniciar la aplicación"
        echo "  status  - Mostrar estado de la aplicación"
        exit 1
        ;;
esac
