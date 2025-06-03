#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para ejecutar la aplicación Flask directamente sin Gunicorn
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Importar la aplicación Flask
try:
    from app import create_app
    app = create_app()
    
    # Configuración de sesión
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    app.config['SESSION_COOKIE_NAME'] = 'edefrutos2025_session'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1 día en segundos
    app.config['SECRET_KEY'] = 'clave_secreta_para_desarrollo'
    
    logger.info("✅ Aplicación Flask creada correctamente")
    logger.info(f"✅ Configuración de sesión aplicada directamente")
    
    # Ejecutar la aplicación
    if __name__ == "__main__":
        port = 5001
        logger.info(f"Iniciando aplicación Flask en el puerto {port}...")
        app.run(host='127.0.0.1', port=port, debug=True)
except Exception as e:
    logger.error(f"❌ Error al crear o ejecutar la aplicación Flask: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
