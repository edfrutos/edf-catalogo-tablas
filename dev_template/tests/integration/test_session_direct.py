#!/usr/bin/env python3
# Script para probar directamente las sesiones en Flask
# Ejecutar con: python test_session_direct.py

from flask import Flask, session, request, redirect
from datetime import datetime
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Crear una aplicación Flask simple para pruebas
app = Flask(__name__)

# Configuración de sesión
app.config['SECRET_KEY'] = 'clave_prueba_sesion_123'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_COOKIE_NAME'] = 'test_session_cookie'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas en segundos
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Asegurarse de que el directorio de sesiones existe
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Inicializar Flask-Session si está disponible
try:
    from flask_session import Session
    Session(app)
    logging.info("Flask-Session inicializado correctamente")
except ImportError:
    logging.warning("Flask-Session no está instalado, usando sesiones predeterminadas de Flask")

@app.route('/')
def index():
    """Ruta principal para probar la persistencia de sesiones."""
    # Añadir un valor a la sesión
    session['prueba_timestamp'] = datetime.now().isoformat()
    session['contador'] = session.get('contador', 0) + 1
    
    # Preparar respuesta HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prueba de Sesión Directa</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>Prueba de Sesión Directa</h1>
            
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Estado de la Sesión</h5>
                </div>
                <div class="card-body">
                    <p><strong>Timestamp:</strong> {session.get('prueba_timestamp', 'No disponible')}</p>
                    <p><strong>Contador:</strong> {session.get('contador', 0)}</p>
                    <p><strong>Sesión Permanente:</strong> {session.permanent}</p>
                    <p><strong>ID de Sesión:</strong> {request.cookies.get(app.config.get('SESSION_COOKIE_NAME', ''), 'No disponible')}</p>
                    
                    <h6 class="mt-3">Contenido completo de la sesión:</h6>
                    <pre>{dict(session)}</pre>
                    
                    <div class="mt-3">
                        <a href="/" class="btn btn-primary">Actualizar</a>
                        <a href="/limpiar" class="btn btn-danger">Limpiar sesión</a>
                    </div>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">Configuración de Sesión</h5>
                </div>
                <div class="card-body">
                    <p><strong>SESSION_TYPE:</strong> {app.config.get('SESSION_TYPE', 'No configurado')}</p>
                    <p><strong>SESSION_FILE_DIR:</strong> {app.config.get('SESSION_FILE_DIR', 'No configurado')}</p>
                    <p><strong>SESSION_COOKIE_NAME:</strong> {app.config.get('SESSION_COOKIE_NAME', 'No configurado')}</p>
                    <p><strong>SESSION_COOKIE_SECURE:</strong> {app.config.get('SESSION_COOKIE_SECURE', False)}</p>
                    <p><strong>SESSION_COOKIE_HTTPONLY:</strong> {app.config.get('SESSION_COOKIE_HTTPONLY', True)}</p>
                    <p><strong>SESSION_COOKIE_SAMESITE:</strong> {app.config.get('SESSION_COOKIE_SAMESITE', 'No configurado')}</p>
                    <p><strong>PERMANENT_SESSION_LIFETIME:</strong> {app.config.get('PERMANENT_SESSION_LIFETIME', 'No configurado')}</p>
                    <p><strong>SECRET_KEY:</strong> {'*' * len(str(app.config.get('SECRET_KEY', '')))}</p>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0">Cookies Recibidas</h5>
                </div>
                <div class="card-body">
                    <pre>{request.cookies}</pre>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/limpiar')
def limpiar():
    """Limpia la sesión actual."""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    logging.info("Iniciando servidor de prueba de sesiones...")
    logging.info(f"Configuración de sesión: {app.config.get('SESSION_TYPE')} en {app.config.get('SESSION_FILE_DIR')}")
    logging.info(f"Nombre de cookie: {app.config.get('SESSION_COOKIE_NAME')}")
    logging.info(f"Cookie segura: {app.config.get('SESSION_COOKIE_SECURE')}")
    app.run(debug=True, host='0.0.0.0', port=5001)
