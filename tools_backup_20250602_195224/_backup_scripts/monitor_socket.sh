#!/bin/bash

# Configuración
SOCKET_PATH="/app.sock"
LOG_FILE="/logs/socket_monitor.log"
APP_USER="www-data"
MAX_LOG_SIZE=10485760 # 10MB en bytes
GUNICORN_SERVICE="gunicorn"
WEB_SERVICE="apache2"  # O "nginx" si estás usando Nginx

# Asegurar que el directorio de logs existe
mkdir -p "$(dirname "$LOG_FILE")"

# Rotar el archivo de log si es demasiado grande
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_SIZE ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
    touch "$LOG_FILE"
    echo "$(date) - Log rotado debido a tamaño excesivo" >> "$LOG_FILE"
fi

# Registrar inicio del chequeo
echo "$(date) - Iniciando verificación del socket para Gunicorn" >> "$LOG_FILE"

# Verificar si el socket existe
if [ ! -S "$SOCKET_PATH" ]; then
    echo "$(date) - ERROR: Socket no encontrado, reiniciando Gunicorn" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
    echo "$(date) - Esperando 5 segundos para que Gunicorn se inicie..." >> "$LOG_FILE"
    sleep 5
    
    # Verificar nuevamente si el socket se ha creado
    if [ ! -S "$SOCKET_PATH" ]; then
        echo "$(date) - ERROR: Socket aún no encontrado, reiniciando servidor web" >> "$LOG_FILE"
        sudo systemctl restart $WEB_SERVICE || echo "$(date) - Error al reiniciar $WEB_SERVICE" >> "$LOG_FILE"
    fi
else
    echo "$(date) - Socket encontrado, verificando permisos" >> "$LOG_FILE"
    
    # Verificar permisos
    PERMS=$(stat -c "%a" "$SOCKET_PATH" 2>/dev/null || echo "000")
    OWNER=$(stat -c "%U" "$SOCKET_PATH" 2>/dev/null || echo "unknown")
    
    echo "$(date) - Permisos actuales: $PERMS, Propietario: $OWNER" >> "$LOG_FILE"
    
    if [ "$PERMS" != "666" ]; then
        echo "$(date) - Corrigiendo permisos del socket" >> "$LOG_FILE"
        sudo chmod 666 "$SOCKET_PATH" || echo "$(date) - Error al cambiar permisos" >> "$LOG_FILE"
    fi
fi

# Verificar procesos de Gunicorn
GUNICORN_COUNT=$(ps aux | grep -E "gunicorn" | grep -v grep | wc -l)
echo "$(date) - Procesos de Gunicorn en ejecución: $GUNICORN_COUNT" >> "$LOG_FILE"

if [ "$GUNICORN_COUNT" -lt 2 ]; then
    echo "$(date) - ADVERTENCIA: Pocos procesos de Gunicorn, reiniciando servicio" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
fi

# Verificar uso de memoria
MEM_USAGE=$(ps aux | grep gunicorn | awk '{sum+=$4} END {print sum}')
echo "$(date) - Uso total de memoria de Gunicorn: $MEM_USAGE%" >> "$LOG_FILE"

# Verificar si el uso de memoria es mayor que 80%
if [ $(echo "$MEM_USAGE > 80" | bc 2>/dev/null) -eq 1 ]; then
    echo "$(date) - ADVERTENCIA: Alto uso de memoria, reiniciando Gunicorn" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
fi

# Verificar si el servicio de Gunicorn está activo
if ! systemctl is-active --quiet $GUNICORN_SERVICE; then
    echo "$(date) - ERROR: Servicio Gunicorn no está activo, iniciándolo" >> "$LOG_FILE"
    sudo systemctl start $GUNICORN_SERVICE || echo "$(date) - Error al iniciar Gunicorn" >> "$LOG_FILE"
fi

# Verificar tiempo de respuesta de la aplicación
echo "$(date) - Verificando tiempo de respuesta..." >> "$LOG_FILE"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --unix-socket $SOCKET_PATH http://localhost/ 2>/dev/null)
RESPONSE_CODE=$?

if [ $RESPONSE_CODE -ne 0 ]; then
    echo "$(date) - ERROR: No se pudo conectar al socket, reiniciando Gunicorn" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
else
    echo "$(date) - Tiempo de respuesta: ${RESPONSE_TIME}s" >> "$LOG_FILE"
    
    # Si el tiempo de respuesta es mayor a 5 segundos, reiniciar Gunicorn
    if [ $(echo "$RESPONSE_TIME > 5.0" | bc 2>/dev/null) -eq 1 ]; then
        echo "$(date) - ADVERTENCIA: Tiempo de respuesta alto, reiniciando Gunicorn" >> "$LOG_FILE"
        sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
    fi
fi

# Verificar conexión a MongoDB
echo "$(date) - Verificando conexión a MongoDB..." >> "$LOG_FILE"
MONGO_STATUS=$(python3 -c "
import sys, os
try:
    import pymongo
    from dotenv import load_dotenv
    load_dotenv('/.env')
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print('ERROR: MONGO_URI no encontrada en .env')
        sys.exit(1)
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('OK')
except ImportError as e:
    print(f'ERROR: Módulo no encontrado: {str(e)}')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
" 2>&1)

echo "$(date) - Estado de MongoDB: $MONGO_STATUS" >> "$LOG_FILE"

# Verificar si la respuesta no comienza con OK
if echo "$MONGO_STATUS" | grep -v "^OK" > /dev/null; then
    echo "$(date) - ADVERTENCIA: Problema con MongoDB, reiniciando Gunicorn" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
fi

# Verificar procesos zombie
ZOMBIES=$(ps aux | grep -w Z | grep -v grep | wc -l)
if [ $ZOMBIES -gt 0 ]; then
    echo "$(date) - ADVERTENCIA: $ZOMBIES procesos zombie detectados" >> "$LOG_FILE"
    
    # Listar procesos zombie para diagnóstico
    ZOMBIE_LIST=$(ps aux | grep -w Z | grep -v grep)
    echo "$(date) - Lista de procesos zombie:" >> "$LOG_FILE"
    echo "$ZOMBIE_LIST" >> "$LOG_FILE"
    
    # Intentar reiniciar Gunicorn para resolver procesos zombie
    echo "$(date) - Reiniciando Gunicorn para resolver procesos zombie" >> "$LOG_FILE"
    sudo systemctl restart $GUNICORN_SERVICE || echo "$(date) - Error al reiniciar Gunicorn" >> "$LOG_FILE"
fi

# Verificar tamaño de archivos de log
LOG_DIR="/logs"
for logfile in "$LOG_DIR"/*.log; do
    if [ -f "$logfile" ]; then
        SIZE_MB=$(du -m "$logfile" | cut -f1)
        if [ $SIZE_MB -gt 100 ]; then  # Si es mayor a 100MB
            echo "$(date) - ADVERTENCIA: Archivo de log grande: $logfile ($SIZE_MB MB)" >> "$LOG_FILE"
            
            # Rotar el archivo de log
            BACKUP="$logfile.$(date +%Y%m%d%H%M%S)"
            mv "$logfile" "$BACKUP"
            touch "$logfile"
            echo "$(date) - Archivo de log rotado a $BACKUP" >> "$LOG_FILE"
        fi
    fi
done

echo "$(date) - Verificación completada" >> "$LOG_FILE"
echo "-------------------------------------------" >> "$LOG_FILE"