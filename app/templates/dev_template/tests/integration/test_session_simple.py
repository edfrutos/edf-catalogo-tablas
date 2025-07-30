#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simple para probar la persistencia de sesiones en Flask.
Este script crea una aplicación Flask independiente con rutas básicas
para probar el funcionamiento de las sesiones.

Ejecución:
    python test_session_simple.py
"""

import os
import logging
from datetime import datetime
from flask import Flask, session, request, jsonify, render_template_string, redirect, url_for
from flask_session import Session

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [TEST_SESSION] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Plantilla HTML simple
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test de Sesión Simple</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Test de Sesión Simple</h1>
    
    <h2>Estado de la Sesión</h2>
    <pre>{{ session_data }}</pre>
    
    <h2>Acciones</h2>
    <p>
        <a href="{{ url_for('set_value') }}">Establecer valor</a> |
        <a href="{{ url_for('clear_session') }}">Limpiar sesión</a>
    </p>
    
    <h2>Cookies</h2>
    <pre>{{ cookies }}</pre>
</body>
</html>
"""

def create_app():
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'clave_test_session_simple'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    app.config['SESSION_COOKIE_NAME'] = 'test_session_simple'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400
    
    # Asegurar que el directorio de sesiones existe
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Inicializar Flask-Session
    Session(app)
    
    @app.route('/')
    def index():
        session_data = dict(session)
        cookies = {k: v for k, v in request.cookies.items()}
        return render_template_string(
            TEMPLATE,
            session_data=session_data,
            cookies=cookies
        )
    
    @app.route('/set_value')
    def set_value():
        session['test_value'] = f"Valor de prueba - {datetime.now().isoformat()}"
        session['timestamp'] = datetime.now().isoformat()
        session.modified = True
        logger.info(f"Valor establecido en la sesión: {session.get('test_value')}")
        return redirect(url_for('index'))
    
    @app.route('/clear_session')
    def clear_session():
        session.clear()
        logger.info("Sesión limpiada")
        return redirect(url_for('index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n✅ Test de sesión simple iniciado en http://localhost:5001/")
    app.run(debug=True, host='0.0.0.0', port=5001)
