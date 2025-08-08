#!/bin/bash
cd "$(dirname "$0")/../.."  # Navegar al directorio raíz del proyecto
git pull
source venv/bin/activate
pip install -r requirements.txt
touch wsgi.py  # Para reiniciar la aplicación