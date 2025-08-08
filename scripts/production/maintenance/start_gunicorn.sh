#!/bin/bash
cd /var/www/vhosts/edefrutos2025.xyz/httpdocs
mkdir -p logs

# Usar el entorno virtual en la ubicación correcta
source /.venv/bin/activate

# Agregar mensajes de depuración
echo "$(date) - Iniciando Gunicorn con wsgi:app (compatible con systemd)" >> logs/startup.log

# Eliminar el socket si ya existe
if [ -e "app.sock" ]; then
    rm -f app.sock
fi

# Ejecutar Gunicorn con wsgi:app (igual que systemd)
gunicorn --bind unix:/app.sock wsgi:app --workers 1 --log-level debug --error-logfile logs/gunicorn_error.log --access-logfile logs/gunicorn_access.log

# Asegurar que el socket sea accesible para Apache
chmod 777 app.sock
