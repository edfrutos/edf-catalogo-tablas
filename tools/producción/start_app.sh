#!/bin/bash

# Activar entorno virtual
source /.venv/bin/activate

# Cambiar al directorio de la aplicación
cd /var/www/vhosts/edefrutos2025.xyz/httpdocs

# Detener cualquier instancia de Gunicorn en ejecución
pkill -f "gunicorn.*app:app"

# Iniciar Gunicorn
/.venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 1 --log-level debug --error-logfile logs/gunicorn_error.log --access-logfile logs/gunicorn_access.log app:app
