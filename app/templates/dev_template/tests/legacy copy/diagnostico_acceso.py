#!/usr/bin/env python3

"""
Script de diagnóstico de acceso a la aplicación
Este script verifica la configuración de la aplicación y proporciona
información detallada sobre el estado actual.
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime

import certifi
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def verificar_mongodb():
    """Verifica la conexión a MongoDB y el usuario administrador"""
    try:
        # Cargar variables de entorno
        load_dotenv()

        # Obtener la URI de MongoDB
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            return {"status": "error", "message": "No se encontró MONGO_URI en las variables de entorno"}

        # Conectar a MongoDB
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1')
        )

        # Verificar conexión
        client.admin.command('ping')

        # Seleccionar base de datos y colección
        db = client["app_catalogojoyero_nueva"]
        users_collection = db["users"]

        # Buscar usuario administrador
        admin_user = users_collection.find_one({"email": "admin@example.com"})

        if admin_user:
            admin_info = {
                "id": str(admin_user.get("_id")),
                "email": admin_user.get("email"),
                "role": admin_user.get("role"),
                "username": admin_user.get("username") or admin_user.get("nombre"),
                "locked_until": admin_user.get("locked_until"),
                "failed_attempts": admin_user.get("failed_attempts")
            }
            return {
                "status": "success",
                "message": "Conexión a MongoDB establecida correctamente",
                "admin_user": admin_info,
                "total_users": users_collection.count_documents({})
            }
        else:
            return {
                "status": "warning",
                "message": "No se encontró el usuario administrador",
                "total_users": users_collection.count_documents({})
            }

    except Exception as e:
        return {"status": "error", "message": f"Error al conectar a MongoDB: {str(e)}"}

def verificar_blueprints():
    """Verifica si los blueprints están registrados correctamente"""
    try:
        # Añadir el directorio actual al path para importar módulos
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Importar la aplicación Flask
        from app import app

        # Obtener información de blueprints
        blueprints = []
        for rule in app.url_map.iter_rules():
            blueprint = rule.endpoint.split('.')[0] if '.' in rule.endpoint else None
            if blueprint and blueprint not in [bp.get('name') for bp in blueprints]:
                blueprints.append({
                    "name": blueprint,
                    "url_prefix": None  # No podemos obtener el prefijo directamente
                })

        # Obtener información de rutas
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "rule": str(rule)
            })

        return {
            "status": "success",
            "message": f"Se encontraron {len(blueprints)} blueprints y {len(routes)} rutas",
            "blueprints": blueprints,
            "routes": routes[:20]  # Limitar a 20 rutas para no saturar la salida
        }

    except Exception as e:
        return {"status": "error", "message": f"Error al verificar blueprints: {str(e)}"}

def verificar_configuracion_sesion():
    """Verifica la configuración de sesiones"""
    try:
        # Añadir el directorio actual al path para importar módulos
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Importar la aplicación Flask
        from app import app

        # Obtener configuración de sesión
        session_config = {
            "SESSION_TYPE": app.config.get("SESSION_TYPE"),
            "SESSION_FILE_DIR": app.config.get("SESSION_FILE_DIR"),
            "SESSION_COOKIE_NAME": app.config.get("SESSION_COOKIE_NAME"),
            "SESSION_COOKIE_SECURE": app.config.get("SESSION_COOKIE_SECURE"),
            "SESSION_COOKIE_HTTPONLY": app.config.get("SESSION_COOKIE_HTTPONLY"),
            "SESSION_COOKIE_SAMESITE": app.config.get("SESSION_COOKIE_SAMESITE"),
            "SESSION_PERMANENT": app.config.get("SESSION_PERMANENT"),
            "PERMANENT_SESSION_LIFETIME": app.config.get("PERMANENT_SESSION_LIFETIME"),
            "SESSION_REFRESH_EACH_REQUEST": app.config.get("SESSION_REFRESH_EACH_REQUEST"),
            "SESSION_USE_SIGNER": app.config.get("SESSION_USE_SIGNER"),
            "SECRET_KEY": "***OCULTO***" if app.config.get("SECRET_KEY") else None
        }

        # Verificar directorio de sesiones
        session_dir = app.config.get("SESSION_FILE_DIR")
        if session_dir and os.path.exists(session_dir):
            session_files = os.listdir(session_dir)
        else:
            session_files = []

        return {
            "status": "success",
            "message": "Configuración de sesión obtenida correctamente",
            "session_config": session_config,
            "session_files_count": len(session_files),
            "session_dir_exists": os.path.exists(session_dir) if session_dir else False
        }

    except Exception as e:
        return {"status": "error", "message": f"Error al verificar configuración de sesión: {str(e)}"}

def crear_app_diagnostico():
    """Crea una aplicación Flask para diagnóstico"""
    app = Flask(__name__)

    # Configuración básica
    app.config['SECRET_KEY'] = 'clave_diagnostico_temporal'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session_diagnostico')
    app.config['SESSION_COOKIE_NAME'] = 'diagnostico_session'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_PERMANENT'] = True

    # Asegurar que el directorio de sesiones existe
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Ruta principal
    @app.route('/')
    def index():
        # Ejecutar verificaciones
        mongodb_info = verificar_mongodb()
        blueprints_info = verificar_blueprints()
        session_info = verificar_configuracion_sesion()

        # Preparar datos para la plantilla
        diagnostico = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mongodb": mongodb_info,
            "blueprints": blueprints_info,
            "session": session_info
        }

        # Plantilla HTML
        template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Diagnóstico de Acceso</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding: 20px; }
                .card { margin-bottom: 20px; }
                pre { background-color: #f8f9fa; padding: 10px; border-radius: 5px; }
                .success { color: green; }
                .warning { color: orange; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4">Diagnóstico de Acceso</h1>
                <p>Fecha y hora: {{ diagnostico.timestamp }}</p>
                
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        Conexión a MongoDB
                    </div>
                    <div class="card-body">
                        <h5 class="card-title {{ diagnostico.mongodb.status }}">
                            Estado: {{ diagnostico.mongodb.status.upper() }}
                        </h5>
                        <p>{{ diagnostico.mongodb.message }}</p>
                        
                        {% if diagnostico.mongodb.status == 'success' %}
                            <h6>Usuario Administrador:</h6>
                            <pre>{{ diagnostico.mongodb.admin_user|tojson(indent=2) }}</pre>
                            <p>Total de usuarios: {{ diagnostico.mongodb.total_users }}</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        Blueprints y Rutas
                    </div>
                    <div class="card-body">
                        <h5 class="card-title {{ diagnostico.blueprints.status }}">
                            Estado: {{ diagnostico.blueprints.status.upper() }}
                        </h5>
                        <p>{{ diagnostico.blueprints.message }}</p>
                        
                        {% if diagnostico.blueprints.status == 'success' %}
                            <h6>Blueprints Registrados:</h6>
                            <pre>{{ diagnostico.blueprints.blueprints|tojson(indent=2) }}</pre>
                            
                            <h6>Rutas Disponibles (primeras 20):</h6>
                            <pre>{{ diagnostico.blueprints.routes|tojson(indent=2) }}</pre>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        Configuración de Sesión
                    </div>
                    <div class="card-body">
                        <h5 class="card-title {{ diagnostico.session.status }}">
                            Estado: {{ diagnostico.session.status.upper() }}
                        </h5>
                        <p>{{ diagnostico.session.message }}</p>
                        
                        {% if diagnostico.session.status == 'success' %}
                            <h6>Configuración:</h6>
                            <pre>{{ diagnostico.session.session_config|tojson(indent=2) }}</pre>
                            
                            <p>Directorio de sesiones existe: {{ diagnostico.session.session_dir_exists }}</p>
                            <p>Número de archivos de sesión: {{ diagnostico.session.session_files_count }}</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-success text-white">
                        Acciones Disponibles
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-info text-white">
                                        Acceso a la Aplicación
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Credenciales de administrador:</strong></p>
                                        <ul>
                                            <li>Email: admin@example.com</li>
                                            <li>Contraseña: admin123</li>
                                        </ul>
                                        <a href="http://127.0.0.1:5001/login" class="btn btn-primary">Ir a la página de login</a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-warning text-dark">
                                        Herramientas de Diagnóstico
                                    </div>
                                    <div class="card-body">
                                        <a href="http://127.0.0.1:5001/test_session" class="btn btn-secondary mb-2">Probar Sesión</a>
                                        <a href="http://127.0.0.1:5001/ping" class="btn btn-secondary mb-2">Verificar Ping</a>
                                        <a href="/" class="btn btn-secondary mb-2">Actualizar Diagnóstico</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Función para convertir a JSON con formato
        def tojson_filter(obj, indent=None):
            return json.dumps(obj, indent=indent, ensure_ascii=False)

        # Renderizar plantilla
        rendered = render_template_string(
            template,
            diagnostico=diagnostico,
            tojson=tojson_filter
        )

        return rendered

    return app

if __name__ == "__main__":
    try:
        app = crear_app_diagnostico()
        logger.info("Iniciando aplicación de diagnóstico en el puerto 5003...")
        app.run(host='0.0.0.0', port=5003, debug=True)
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
