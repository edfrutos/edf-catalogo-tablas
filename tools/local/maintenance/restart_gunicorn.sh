#!/bin/bash
# Script para reiniciar Gunicorn con limpieza de recursos
# Fecha: 2025-05-20

# Directorio base
BASE_DIR="$(dirname "$0")/../.."  # Directorio raíz del proyecto
LOG_DIR="$BASE_DIR/logs"
PID_FILE="$LOG_DIR/gunicorn.pid"

# Asegurar que estamos en el directorio correcto
cd $BASE_DIR || exit 1

# Crear el directorio de logs si no existe
mkdir -p $LOG_DIR

# Función para matar procesos Gunicorn existentes
kill_gunicorn() {
    echo "Buscando procesos Gunicorn activos..."
    # Buscar procesos Gunicorn por el nombre de la aplicación
    GUNICORN_PIDS=$(ps aux | grep -i "gunicorn.*edefrutos" | grep -v grep | awk '{print $2}')
    
    if [ -n "$GUNICORN_PIDS" ]; then
        echo "Matando procesos Gunicorn: $GUNICORN_PIDS"
        kill -9 $GUNICORN_PIDS 2>/dev/null
        sleep 2
    else
        echo "No se encontraron procesos Gunicorn activos"
    fi
    
    # También probar con el archivo PID si existe
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if [ -n "$PID" ]; then
            echo "Matando proceso Gunicorn desde PID_FILE: $PID"
            kill -9 $PID 2>/dev/null
            rm -f "$PID_FILE"
        fi
    fi
}

# Función para limpiar recursos del sistema
clean_resources() {
    echo "Limpiando recursos del sistema..."
    
    # Limpieza de archivos temporales
    find /tmp -name "gunicorn-*" -type f -delete
    find /tmp -name "edefrutos*" -type f -delete
    
    # Limpiar sockets abandonados
    find /tmp -name "*.sock" -type s -delete
    
    # Limpiar logs muy grandes (más de 10MB)
    find $LOG_DIR -type f -name "*.log" -size +10M -exec truncate -s 1M {} \;
    
    # Vaciar cache del sistema
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    
    # Esperar un momento para que el sistema se estabilice
    sleep 3
}

# Matar procesos existentes
kill_gunicorn

# Limpiar recursos
clean_resources

# Activar entorno virtual
source .venv/bin/activate

# Iniciar Gunicorn con la configuración optimizada
echo "Iniciando Gunicorn con configuración optimizada..."
nohup gunicorn --config=gunicorn_config.py wsgi:app >> $LOG_DIR/gunicorn_startup.log 2>&1 &

# Guardar el PID
echo $! > $PID_FILE

# Verificar si está corriendo
sleep 5
if ps -p $(cat $PID_FILE) > /dev/null; then
    echo "Gunicorn se ha iniciado correctamente con PID: $(cat $PID_FILE)"
    exit 0
else
    echo "Error al iniciar Gunicorn. Revisar logs en $LOG_DIR/gunicorn_startup.log"
    exit 1
fi
