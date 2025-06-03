#!/bin/bash

# Este script inicia la aplicación Flask en modo producción
# usando Gunicorn directamente sin depender del servicio systemd

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
$APP_DIR/.venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 1 --log-level debug --error-logfile $APP_DIR/logs/gunicorn_error.log --access-logfile $APP_DIR/logs/gunicorn_access.log wsgi:app
