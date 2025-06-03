#!/bin/bash

# Este script inicia la aplicación Flask localmente para pruebas
# No afecta a la configuración del servidor

# Directorio de la aplicación
APP_DIR="/var/www/vhosts/edefrutos2025.xyz/httpdocs"

# Activar entorno virtual
source $APP_DIR/.venv/bin/activate

# Cambiar al directorio de la aplicación
cd $APP_DIR

# Detener cualquier instancia anterior
pkill -f "python.*app.py" || true
pkill -f "flask run" || true

# Iniciar la aplicación en modo desarrollo
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Iniciar en puerto 5000 (solo accesible localmente)
flask run --host=127.0.0.1 --port=5000
