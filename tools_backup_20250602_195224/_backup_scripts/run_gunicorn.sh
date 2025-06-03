#!/bin/bash
cd /var/www/vhosts/edefrutos2025.xyz/httpdocs
source /.venv/bin/activate
mkdir -p logs
gunicorn --bind unix:/app.sock wsgi:application --error-logfile logs/gunicorn_error.log --access-logfile logs/gunicorn_access.log --capture-output --daemon
