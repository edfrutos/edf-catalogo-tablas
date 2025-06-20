#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de diagnóstico para verificar y solucionar problemas de sesión en la aplicación Flask.
Este script crea una aplicación Flask independiente que muestra información detallada sobre
la configuración de sesiones y permite probar diferentes soluciones.

Ejecución:
    python diagnostico_sesion.py

Acceso:
    http://localhost:5050/
"""

import os
import sys
import json
import logging
import tempfile
import traceback
import secrets
from datetime import datetime, timedelta
from flask import Flask, session, request, jsonify, render_template_string, redirect, url_for
from flask_session import Session

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [DIAGNOSTICO] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Plantilla HTML para mostrar información de diagnóstico
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Diagnóstico de Sesión</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        .success { color: green; }
        .error { color: red; }
        .warning { color: orange; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1>Diagnóstico de Sesión</h1>
        
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Estado de la Sesión</h5>
            </div>
            <div class="card-body">
                <p><strong>ID de Sesión:</strong> {{ session_id }}</p>
                <p><strong>Sesión Permanente:</strong> {{ session_permanent }}</p>
                <p><strong>Contenido de la Sesión:</strong></p>
                <pre>{{ session_data }}</pre>
                
                <div class="mt-3">
                    <a href="{{ url_for('set_session_value') }}" class="btn btn-success">Establecer Valor de Prueba</a>
                    <a href="{{ url_for('clear_session') }}" class="btn btn-danger">Limpiar Sesión</a>
                </div>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">Configuración de Flask</h5>
            </div>
            <div class="card-body">
                <p><strong>SECRET_KEY:</strong> {{ secret_key_info }}</p>
                <p><strong>SESSION_TYPE:</strong> {{ session_type }}</p>
                <p><strong>SESSION_FILE_DIR:</strong> {{ session_file_dir }}</p>
                <p><strong>SESSION_COOKIE_NAME:</strong> {{ session_cookie_name }}</p>
                <p><strong>SESSION_COOKIE_SECURE:</strong> {{ session_cookie_secure }}</p>
                <p><strong>SESSION_COOKIE_HTTPONLY:</strong> {{ session_cookie_httponly }}</p>
                <p><strong>SESSION_COOKIE_SAMESITE:</strong> {{ session_cookie_samesite }}</p>
                <p><strong>PERMANENT_SESSION_LIFETIME:</strong> {{ permanent_session_lifetime }}</p>
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
        
        <div class="card mb-4">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">Información del Sistema</h5>
            </div>
            <div class="card-body">
                <p><strong>Python:</strong> {{ python_version }}</p>
                <p><strong>Flask:</strong> {{ flask_version }}</p>
                <p><strong>Directorio de Trabajo:</strong> {{ working_dir }}</p>
                <p><strong>Permisos del Directorio de Sesiones:</strong> {{ session_dir_permissions }}</p>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">Acciones de Diagnóstico</h5>
            </div>
            <div class="card-body">
                <a href="{{ url_for('test_login') }}" class="btn btn-primary">Simular Login</a>
                <a href="{{ url_for('test_admin') }}" class="btn btn-danger">Simular Login Admin</a>
                <a href="{{ url_for('fix_permissions') }}" class="btn btn-warning">Reparar Permisos</a>
                <a href="{{ url_for('check_blueprints') }}" class="btn btn-info">Verificar Blueprints</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

def create_diagnostic_app():
    """Crea una aplicación Flask para diagnóstico de sesiones."""
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'clave_diagnostico_segura_123'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    app.config['SESSION_COOKIE_NAME'] = 'diagnostico_session'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400
    
    # Asegurar que el directorio de sesiones existe
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Inicializar Flask-Session si está disponible
    try:
        from flask_session import Session
        Session(app)
        logger.info("Flask-Session inicializado correctamente")
    except ImportError:
        logger.warning("Flask-Session no está instalado, usando sesiones basadas en cookies")
    
    @app.route('/')
    def index():
        """Página principal de diagnóstico."""
        # Información de la sesión
        session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'], 'No disponible')
        session_permanent = session.permanent if hasattr(session, 'permanent') else False
        session_data = json.dumps(dict(session), indent=2) if session else '{}'
        
        # Información de configuración
        secret_key_info = f"{type(app.config['SECRET_KEY']).__name__} de longitud {len(str(app.config['SECRET_KEY']))}"
        session_type = app.config.get('SESSION_TYPE', 'No configurado')
        session_file_dir = app.config.get('SESSION_FILE_DIR', 'No configurado')
        session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'No configurado')
        session_cookie_secure = app.config.get('SESSION_COOKIE_SECURE', False)
        session_cookie_httponly = app.config.get('SESSION_COOKIE_HTTPONLY', True)
        session_cookie_samesite = app.config.get('SESSION_COOKIE_SAMESITE', 'No configurado')
        permanent_session_lifetime = str(app.config.get('PERMANENT_SESSION_LIFETIME', 'No configurado'))
        
        # Información de cookies
        cookies = json.dumps({k: v for k, v in request.cookies.items()}, indent=2)
        
        # Información del sistema
        import platform
        import flask
        python_version = platform.python_version()
        flask_version = flask.__version__
        working_dir = os.getcwd()
        
        # Verificar permisos del directorio de sesiones
        session_dir = app.config.get('SESSION_FILE_DIR', '')
        if os.path.exists(session_dir):
            import stat
            st = os.stat(session_dir)
            permissions = oct(st.st_mode)[-3:]
            owner = st.st_uid
            group = st.st_gid
            session_dir_permissions = f"Permisos: {permissions}, UID: {owner}, GID: {group}"
        else:
            session_dir_permissions = "Directorio no existe"
        
        return render_template_string(
            TEMPLATE,
            session_id=session_id,
            session_permanent=session_permanent,
            session_data=session_data,
            secret_key_info=secret_key_info,
            session_type=session_type,
            session_file_dir=session_file_dir,
            session_cookie_name=session_cookie_name,
            session_cookie_secure=session_cookie_secure,
            session_cookie_httponly=session_cookie_httponly,
            session_cookie_samesite=session_cookie_samesite,
            permanent_session_lifetime=permanent_session_lifetime,
            cookies=cookies,
            python_version=python_version,
            flask_version=flask_version,
            working_dir=working_dir,
            session_dir_permissions=session_dir_permissions
        )
    
    @app.route('/set_session_value')
    def set_session_value():
        """Establece un valor de prueba en la sesión."""
        session['test_value'] = f"Valor de prueba - {datetime.now().isoformat()}"
        session['timestamp'] = datetime.now().isoformat()
        session.permanent = True
        logger.info(f"Valor de prueba establecido en la sesión: {session.get('test_value')}")
        return redirect(url_for('index'))
    
    @app.route('/clear_session')
    def clear_session():
        """Limpia la sesión actual."""
        session.clear()
        logger.info("Sesión limpiada")
        return redirect(url_for('index'))
    
    @app.route('/test_login')
    def test_login():
        """Simula un inicio de sesión de usuario normal."""
        session.clear()
        session['user_id'] = '12345'
        session['username'] = 'usuario_prueba'
        session['email'] = 'usuario@example.com'
        session['role'] = 'user'
        session['logged_in'] = True
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True
        logger.info(f"Sesión de usuario simulada: {session.get('username')}")
        return redirect(url_for('index'))
    
    @app.route('/test_admin')
    def test_admin():
        """Simula un inicio de sesión de administrador."""
        session.clear()
        session['user_id'] = 'admin123'
        session['username'] = 'admin'
        session['email'] = 'admin@example.com'
        session['role'] = 'admin'
        session['logged_in'] = True
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True
        logger.info(f"Sesión de administrador simulada: {session.get('username')}")
        return redirect(url_for('index'))
    
    @app.route('/fix_permissions')
    def fix_permissions():
        """Repara los permisos del directorio de sesiones."""
        session_dir = app.config.get('SESSION_FILE_DIR', '')
        if os.path.exists(session_dir):
            try:
                # Cambiar permisos a 755 (rwxr-xr-x)
                os.chmod(session_dir, 0o755)
                logger.info(f"Permisos del directorio de sesiones reparados: {session_dir}")
                return jsonify({"status": "success", "message": "Permisos reparados correctamente"})
            except Exception as e:
                logger.error(f"Error al reparar permisos: {str(e)}")
                return jsonify({"status": "error", "message": f"Error: {str(e)}"})
        else:
            return jsonify({"status": "error", "message": "El directorio de sesiones no existe"})
    
    @app.route('/check_blueprints')
    def check_blueprints():
        """Verifica los blueprints registrados en la aplicación principal."""
        try:
            # Importar la aplicación principal
            from app import app as main_app
            
            # Obtener información de los blueprints
            blueprints = []
            for blueprint_name, blueprint in main_app.blueprints.items():
                blueprints.append({
                    "name": blueprint_name,
                    "url_prefix": blueprint.url_prefix,
                    "static_folder": blueprint.static_folder,
                    "template_folder": blueprint.template_folder
                })
            
            return jsonify({
                "status": "success",
                "blueprints": blueprints,
                "total": len(blueprints)
            })
        except Exception as e:
            logger.error(f"Error al verificar blueprints: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al verificar blueprints: {str(e)}"
            })
    
    @app.route('/test_blueprint_registration')
    def test_blueprint_registration():
        """Prueba la importación y registro de blueprints de diagnóstico."""
        try:
            # Intentar importar los blueprints de diagnóstico
            from app.routes.diagnostico import diagnostico_bp
            from app.routes.test_session import test_session_bp
            
            # Verificar las rutas registradas en cada blueprint
            diagnostico_routes = []
            for rule in diagnostico_bp.deferred_functions:
                diagnostico_routes.append(str(rule))
            
            test_session_routes = []
            for rule in test_session_bp.deferred_functions:
                test_session_routes.append(str(rule))
            
            return jsonify({
                "status": "success",
                "diagnostico_bp": {
                    "name": diagnostico_bp.name,
                    "url_prefix": diagnostico_bp.url_prefix,
                    "routes": diagnostico_routes
                },
                "test_session_bp": {
                    "name": test_session_bp.name,
                    "url_prefix": test_session_bp.url_prefix,
                    "routes": test_session_routes
                }
            })
        except Exception as e:
            logger.error(f"Error al probar registro de blueprints: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al probar registro de blueprints: {str(e)}",
                "traceback": traceback.format_exc()
            })

    @app.route('/test_session_persistence')
    def test_session_persistence():
        """Prueba la persistencia de la sesión estableciendo un valor y redirigiendo."""
        session['test_persistence'] = datetime.now().isoformat()
        session.modified = True
        logger.info(f"Valor de prueba de persistencia establecido: {session.get('test_persistence')}")
        return redirect(url_for('check_session_persistence'))

    @app.route('/check_session_persistence')
    def check_session_persistence():
        """Verifica si el valor establecido en la sesión persiste después de la redirección."""
        test_value = session.get('test_persistence', 'No encontrado')
        logger.info(f"Valor de prueba de persistencia recuperado: {test_value}")
        return jsonify({
            "status": "success" if test_value != 'No encontrado' else "error",
            "test_value": test_value,
            "session_data": dict(session)
        })

    @app.route('/fix_session_config')
    def fix_session_config():
        """Intenta corregir la configuración de sesión en la aplicación principal."""
        try:
            # Crear un archivo de configuración temporal con la configuración correcta
            config_content = """\
# Configuración de sesión corregida para Flask
# Generado por el script de diagnóstico

SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = 'flask_session'
SESSION_COOKIE_NAME = 'edefrutos2025_session'
SESSION_COOKIE_SECURE = False  # Deshabilitado para desarrollo
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = 86400  # 24 horas en segundos

# Clave secreta fija para desarrollo
SECRET_KEY = 'desarrollo_clave_secreta_fija_12345'
"""
            
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_config.py')
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            return jsonify({
                "status": "success",
                "message": f"Archivo de configuración de sesión creado en {config_path}",
                "instructions": "Añade 'from session_config import *' al principio de tu archivo app.py para aplicar esta configuración."
            })
        except Exception as e:
            logger.error(f"Error al crear archivo de configuración: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al crear archivo de configuración: {str(e)}"
            })
    
    return app



if __name__ == '__main__':
    app = create_diagnostic_app()
    print(f"\n\n✅ Herramienta de diagnóstico de sesión iniciada en http://localhost:5001/")
    print("📝 Usa esta herramienta para diagnosticar y solucionar problemas de sesión en tu aplicación Flask.")
    print("🔍 Accede a la herramienta desde tu navegador para ver información detallada.\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
