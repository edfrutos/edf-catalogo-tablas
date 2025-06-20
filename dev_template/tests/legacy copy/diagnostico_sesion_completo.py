#!/usr/bin/env python3
# Script de diagnóstico completo para problemas de sesión en Flask
# Ejecutar con: python diagnostico_sesion_completo.py

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from flask import Flask, session, request, redirect, jsonify, make_response

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def verificar_instalacion_flask_session():
    """Verifica si Flask-Session está instalado correctamente"""
    try:
        import flask_session
        logging.info(f"✅ Flask-Session está instalado: {flask_session.__version__}")
        return True
    except ImportError:
        logging.error("❌ Flask-Session no está instalado")
        return False
    except Exception as e:
        logging.error(f"❌ Error al verificar Flask-Session: {e}")
        return False

def verificar_directorio_sesiones(directorio):
    """Verifica si el directorio de sesiones existe y tiene permisos correctos"""
    try:
        if not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
            logging.info(f"✅ Directorio de sesiones creado: {directorio}")
        else:
            logging.info(f"✅ Directorio de sesiones existe: {directorio}")
        
        # Verificar permisos
        if os.access(directorio, os.R_OK | os.W_OK):
            logging.info(f"✅ Permisos correctos en directorio de sesiones")
        else:
            logging.warning(f"⚠️ Permisos insuficientes en directorio de sesiones")
            
        # Listar archivos de sesión
        archivos = os.listdir(directorio)
        logging.info(f"📁 Archivos de sesión encontrados: {len(archivos)}")
        for archivo in archivos[:5]:  # Mostrar solo los primeros 5
            ruta_completa = os.path.join(directorio, archivo)
            tamaño = os.path.getsize(ruta_completa)
            modificado = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
            logging.info(f"   - {archivo} ({tamaño} bytes, modificado: {modificado})")
        
        if len(archivos) > 5:
            logging.info(f"   ... y {len(archivos) - 5} archivos más")
            
        return True
    except Exception as e:
        logging.error(f"❌ Error al verificar directorio de sesiones: {e}")
        logging.error(traceback.format_exc())
        return False

def crear_app_diagnostico():
    """Crea una aplicación Flask para diagnóstico de sesiones"""
    app = Flask(__name__)
    
    # Cargar configuración de sesión desde session_config.py si existe
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import session_config
        for key in dir(session_config):
            if key.startswith('SESSION_') or key in ('SECRET_KEY', 'PERMANENT_SESSION_LIFETIME'):
                app.config[key] = getattr(session_config, key)
        logging.info("✅ Configuración cargada desde session_config.py")
    except ImportError:
        logging.warning("⚠️ No se pudo cargar session_config.py, usando configuración predeterminada")
        # Configuración predeterminada
        app.config['SECRET_KEY'] = 'clave_diagnostico_sesion_123'
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = 'flask_session'
        app.config['SESSION_COOKIE_NAME'] = 'diagnostico_session'
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas
        app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    except Exception as e:
        logging.error(f"❌ Error al cargar session_config.py: {e}")
        logging.error(traceback.format_exc())
        # Configuración de emergencia
        app.config['SECRET_KEY'] = 'clave_emergencia_123'
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = 'flask_session_emergencia'
    
    # Asegurarse de que el directorio de sesiones existe
    if 'SESSION_FILE_DIR' in app.config and not os.path.isabs(app.config['SESSION_FILE_DIR']):
        app.config['SESSION_FILE_DIR'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            app.config['SESSION_FILE_DIR']
        )
    
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Inicializar Flask-Session
    try:
        from flask_session import Session
        Session(app)
        logging.info("✅ Flask-Session inicializado correctamente")
    except ImportError:
        logging.warning("⚠️ Flask-Session no está instalado, usando sesiones predeterminadas de Flask")
    except Exception as e:
        logging.error(f"❌ Error al inicializar Flask-Session: {e}")
        logging.error(traceback.format_exc())
    
    # Rutas de diagnóstico
    @app.route('/')
    def index():
        """Página principal de diagnóstico"""
        # Añadir valores a la sesión
        session['diagnostico_timestamp'] = datetime.now().isoformat()
        session['contador'] = session.get('contador', 0) + 1
        session.modified = True
        
        # Preparar respuesta HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Diagnóstico de Sesión</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>Diagnóstico de Sesión</h1>
                
                <div class="alert alert-info">
                    <p>Este es un diagnóstico de sesión para la aplicación Flask.</p>
                    <p>Si el contador aumenta al recargar la página, las sesiones están funcionando correctamente.</p>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Estado de la Sesión</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Timestamp:</strong> {session.get('diagnostico_timestamp', 'No disponible')}</p>
                        <p><strong>Contador:</strong> {session.get('contador', 0)}</p>
                        <p><strong>Sesión Permanente:</strong> {session.permanent}</p>
                        <p><strong>ID de Sesión:</strong> {request.cookies.get(app.config.get('SESSION_COOKIE_NAME', ''), 'No disponible')}</p>
                        
                        <h6 class="mt-3">Contenido completo de la sesión:</h6>
                        <pre>{dict(session)}</pre>
                        
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
                        <p><strong>SESSION_TYPE:</strong> {app.config.get('SESSION_TYPE', 'No configurado')}</p>
                        <p><strong>SESSION_FILE_DIR:</strong> {app.config.get('SESSION_FILE_DIR', 'No configurado')}</p>
                        <p><strong>SESSION_COOKIE_NAME:</strong> {app.config.get('SESSION_COOKIE_NAME', 'No configurado')}</p>
                        <p><strong>SESSION_COOKIE_SECURE:</strong> {app.config.get('SESSION_COOKIE_SECURE', False)}</p>
                        <p><strong>SESSION_COOKIE_HTTPONLY:</strong> {app.config.get('SESSION_COOKIE_HTTPONLY', True)}</p>
                        <p><strong>SESSION_COOKIE_SAMESITE:</strong> {app.config.get('SESSION_COOKIE_SAMESITE', 'No configurado')}</p>
                        <p><strong>SESSION_REFRESH_EACH_REQUEST:</strong> {app.config.get('SESSION_REFRESH_EACH_REQUEST', False)}</p>
                        <p><strong>SESSION_USE_SIGNER:</strong> {app.config.get('SESSION_USE_SIGNER', False)}</p>
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
                
                <div class="card mb-4">
                    <div class="card-header bg-dark text-white">
                        <h5 class="mb-0">Información del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Flask:</strong> {app.version}</p>
                        <p><strong>Python:</strong> {sys.version}</p>
                        <p><strong>Directorio de trabajo:</strong> {os.getcwd()}</p>
                        <p><strong>Directorio del script:</strong> {os.path.dirname(os.path.abspath(__file__))}</p>
                        <p><strong>Hora del servidor:</strong> {datetime.now().isoformat()}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    @app.route('/limpiar')
    def limpiar():
        """Limpia la sesión actual"""
        session.clear()
        return redirect('/')
    
    @app.route('/test-cookie')
    def test_cookie():
        """Prueba la configuración de cookies"""
        resp = make_response(redirect('/'))
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
                'python_version': sys.version,
                'working_dir': os.getcwd(),
                'script_dir': os.path.dirname(os.path.abspath(__file__)),
                'server_time': datetime.now().isoformat()
            }
        }
        # Ocultar la clave secreta
        if 'SECRET_KEY' in info['config']:
            info['config']['SECRET_KEY'] = '*' * len(str(info['config']['SECRET_KEY']))
        
        return jsonify(info)
    
    return app

def ejecutar_diagnostico():
    """Ejecuta el diagnóstico completo de sesiones"""
    logging.info("🔍 Iniciando diagnóstico de sesiones...")
    
    # Verificar instalación de Flask-Session
    verificar_instalacion_flask_session()
    
    # Verificar directorio de sesiones
    directorio_sesiones = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'flask_session'
    )
    verificar_directorio_sesiones(directorio_sesiones)
    
    # Crear y ejecutar la aplicación de diagnóstico
    app = crear_app_diagnostico()
    
    logging.info("✅ Diagnóstico completado. Iniciando servidor de prueba...")
    logging.info("📌 Accede a http://localhost:5002 para ver los resultados")
    
    return app

if __name__ == '__main__':
    app = ejecutar_diagnostico()
    app.run(debug=True, host='0.0.0.0', port=5002)
