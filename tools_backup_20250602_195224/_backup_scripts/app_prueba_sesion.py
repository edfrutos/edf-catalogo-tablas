#!/usr/bin/env python3
# Aplicación Flask independiente para probar sesiones
# Ejecutar con: python app_prueba_sesion.py

from flask import Flask, session, request, redirect, jsonify, render_template_string
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

# Crear aplicación Flask
app = Flask(__name__)

# Configuración de sesión
app.config['SECRET_KEY'] = 'clave_prueba_sesion_123'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session_prueba')
app.config['SESSION_COOKIE_NAME'] = 'prueba_session'
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
    logging.info("✅ Flask-Session inicializado correctamente")
except ImportError:
    logging.warning("⚠️ Flask-Session no está instalado, usando sesiones predeterminadas de Flask")

# Plantilla HTML para la página principal
TEMPLATE_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Prueba de Sesión</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Prueba de Sesión</h1>
        
        <div class="alert alert-info">
            <p>Esta es una aplicación independiente para probar sesiones en Flask.</p>
            <p>Si el contador aumenta al recargar la página, las sesiones están funcionando correctamente.</p>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Estado de la Sesión</h5>
            </div>
            <div class="card-body">
                <p><strong>Timestamp:</strong> {{ session.get('timestamp', 'No disponible') }}</p>
                <p><strong>Contador:</strong> {{ session.get('contador', 0) }}</p>
                <p><strong>Sesión Permanente:</strong> {{ session.permanent }}</p>
                <p><strong>ID de Sesión:</strong> {{ request.cookies.get(config.get('SESSION_COOKIE_NAME', ''), 'No disponible') }}</p>
                
                <h6 class="mt-3">Contenido completo de la sesión:</h6>
                <pre>{{ session_dict }}</pre>
                
                <div class="mt-3">
                    <a href="/" class="btn btn-primary">Recargar</a>
                    <a href="/limpiar" class="btn btn-danger">Limpiar sesión</a>
                    <a href="/test-cookie" class="btn btn-warning">Probar Cookie</a>
                    <a href="/api/info" class="btn btn-info">Ver JSON</a>
                </div>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">Configuración de Sesión</h5>
            </div>
            <div class="card-body">
                <p><strong>SESSION_TYPE:</strong> {{ config.get('SESSION_TYPE', 'No configurado') }}</p>
                <p><strong>SESSION_FILE_DIR:</strong> {{ config.get('SESSION_FILE_DIR', 'No configurado') }}</p>
                <p><strong>SESSION_COOKIE_NAME:</strong> {{ config.get('SESSION_COOKIE_NAME', 'No configurado') }}</p>
                <p><strong>SESSION_COOKIE_SECURE:</strong> {{ config.get('SESSION_COOKIE_SECURE', False) }}</p>
                <p><strong>SESSION_COOKIE_HTTPONLY:</strong> {{ config.get('SESSION_COOKIE_HTTPONLY', True) }}</p>
                <p><strong>SESSION_COOKIE_SAMESITE:</strong> {{ config.get('SESSION_COOKIE_SAMESITE', 'No configurado') }}</p>
                <p><strong>PERMANENT_SESSION_LIFETIME:</strong> {{ config.get('PERMANENT_SESSION_LIFETIME', 'No configurado') }}</p>
                <p><strong>SECRET_KEY:</strong> {{ '*' * len(str(config.get('SECRET_KEY', ''))) }}</p>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">Cookies Recibidas</h5>
            </div>
            <div class="card-body">
                <pre>{{ cookies }}</pre>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal para probar la persistencia de sesiones"""
    # Añadir valores a la sesión
    session['timestamp'] = datetime.now().isoformat()
    session['contador'] = session.get('contador', 0) + 1
    
    # Preparar datos para la plantilla
    return render_template_string(
        TEMPLATE_INDEX,
        session=session,
        session_dict=dict(session),
        config=app.config,
        cookies=request.cookies
    )

@app.route('/limpiar')
def limpiar():
    """Limpia la sesión actual"""
    session.clear()
    return redirect('/')

@app.route('/test-cookie')
def test_cookie():
    """Prueba la configuración de cookies"""
    resp = redirect('/')
    resp.set_cookie('test_cookie', 'valor_de_prueba', max_age=3600)
    return resp

@app.route('/api/info')
def api_info():
    """Devuelve información de diagnóstico en formato JSON"""
    info = {
        'session': dict(session),
        'cookies': {k: v for k, v in request.cookies.items()},
        'config': {
            k: str(v) for k, v in app.config.items() 
            if k.startswith('SESSION_') or k in ('SECRET_KEY', 'PERMANENT_SESSION_LIFETIME')
        },
        'system': {
            'flask_version': app.version,
            'server_time': datetime.now().isoformat()
        }
    }
    # Ocultar la clave secreta
    if 'SECRET_KEY' in info['config']:
        info['config']['SECRET_KEY'] = '*' * len(str(info['config']['SECRET_KEY']))
    
    return jsonify(info)

if __name__ == '__main__':
    logging.info("🚀 Iniciando aplicación de prueba de sesiones...")
    logging.info(f"📁 Directorio de sesiones: {app.config['SESSION_FILE_DIR']}")
    logging.info(f"🍪 Nombre de cookie: {app.config['SESSION_COOKIE_NAME']}")
    logging.info(f"🔒 Cookie segura: {app.config['SESSION_COOKIE_SECURE']}")
    app.run(debug=True, host='0.0.0.0', port=5001)
