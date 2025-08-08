#!/bin/bash
cd /var/www/vhosts/edefrutos2025.xyz/httpdocs
git pull
source venv/bin/activate
pip install -r requirements.txt
touch wsgi.py  # Para reiniciar la aplicación