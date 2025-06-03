#!/bin/bash

# Este script inicia la aplicación Flask directamente en el puerto 8002
# para que Apache pueda acceder a ella

# Directorio de la aplicación
APP_DIR="/var/www/vhosts/edefrutos2025.xyz/httpdocs"

# Activar entorno virtual
source $APP_DIR/.venv/bin/activate

# Cambiar al directorio de la aplicación
cd $APP_DIR

# Detener cualquier instancia anterior
pkill -f "gunicorn.*wsgi:app" || true

# Crear directorio de logs si no existe
mkdir -p $APP_DIR/logs

# Iniciar Gunicorn en modo producción
nohup $APP_DIR/.venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 1 --log-level debug --error-logfile $APP_DIR/logs/gunicorn_error.log --access-logfile $APP_DIR/logs/gunicorn_access.log wsgi:app > $APP_DIR/logs/app.log 2>&1 &

echo "Aplicación iniciada en segundo plano. Logs en $APP_DIR/logs/app.log"
echo "Para verificar si está en ejecución, ejecuta: curl -I http://127.0.0.1:8002"
