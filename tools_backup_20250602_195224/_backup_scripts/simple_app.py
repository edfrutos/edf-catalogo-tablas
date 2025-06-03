#!/usr/bin/env python3
from flask import Flask, send_from_directory

app = Flask(__name__, static_url_path='/static', static_folder='static')

@app.route('/')
def hello():
    return 'Aplicación Flask simple funcionando correctamente!'

@app.route('/info')
def info():
    import sys
    import os
    html = "<h1>Información de depuración</h1>"
    html += f"<p>Python version: {sys.version}</p>"
    html += f"<p>Working directory: {os.getcwd()}</p>"
    html += f"<p>PYTHONPATH: {sys.path}</p>"
    return html

import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    filename='/flask.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Añadir el directorio actual al path
sys.path.insert(0, '/var/www/vhosts/edefrutos2025.xyz/httpdocs')

logging.info("Iniciando wsgi.py")
logging.info(f"Python version: {sys.version}")
logging.info(f"Working directory: {os.getcwd()}")

# Importar la aplicación simple
try:
    logging.info("Intentando importar simple_app.py")
    from simple_app import app as application
    logging.info("Aplicación importada correctamente")
except Exception as e:
    logging.error(f"Error al importar aplicación: {str(e)}")
    import traceback
    logging.error(traceback.format_exc())
    
    # Crear aplicación de emergencia
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"Error al cargar la aplicación: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True, port=5001)
