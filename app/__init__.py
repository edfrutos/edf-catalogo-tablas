# app/__init__.py

import os
import logging
from flask import Flask, session
from flask_login import LoginManager
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException
from logging.handlers import RotatingFileHandler
from flask_mail import Mail
from config import Config
from datetime import timedelta
from app.logging_config import setup_logging
import secrets

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar el cliente de S3 si está habilitado
use_s3 = os.environ.get('USE_S3', 'false').lower() == 'true'
if use_s3:
    try:
        # Importar boto3 y verificar que esté instalado
        import boto3
        logging.info("AWS S3 está habilitado y boto3 está instalado correctamente")
    except ImportError:
        logging.error("AWS S3 está habilitado pero boto3 no está instalado. Instálelo con 'pip install boto3'")
        # No detener la aplicación, simplemente deshabilitar S3
        os.environ['USE_S3'] = 'false'

# Importar blueprints fuera de la función
from .routes.main_routes import main_bp
from .routes.admin_routes import admin_bp, admin_logs_bp
from .routes.auth_routes import auth_bp
from .routes.maintenance_routes import maintenance_bp
from .routes.catalogs_routes import catalogs_bp
from .routes.catalog_images_routes import image_bp
from .routes.images_routes import images_bp  # Blueprint para /imagenes_subidas/<filename> (ahora llamado uploaded_images)
from .routes.usuarios_routes import usuarios_bp
from .error_handlers import errors_bp
from .routes.emergency_access import emergency_bp
from .routes.scripts_routes import scripts_bp
from .routes.scripts_tools_routes import scripts_tools_bp
from .routes.dev_template import bp_dev_template

# Importar filtros personalizados
from app.filters import init_app as init_filters

# Definir instancias de MongoDB para uso posterior
client = None
db = None

def create_app(testing=False):
    import os
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        static_url_path="/static"
    )
    if testing:
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # Si usas Flask-WTF


    # Configurar clave secreta para sesiones
    app.secret_key = os.getenv('SECRET_KEY', 'edf_secret_key_2025')
    
    # Configuración simplificada usando el sistema de sesiones integrado de Flask
    app.config.update(
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        SESSION_COOKIE_SECURE=False,  # Para pruebas, ponlo en True solo si usas HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_REFRESH_EACH_REQUEST=True,
        SESSION_COOKIE_NAME='edefrutos2025_session',
        SESSION_COOKIE_DOMAIN=None
    )
    
    # Cargar configuración desde config.py
    app.config.from_object('config.Config')
    # Forzar uso de SECRET_KEY y configuración de sesión
    app.secret_key = app.config['SECRET_KEY']
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Inicializar conexión a MongoDB usando el nuevo módulo de base de datos
    global client, db
    
    # Importamos el módulo de base de datos que maneja las conexiones de forma resiliente
    app.logger.info("Inicializando conexión a MongoDB usando el módulo database.py...")
    from app.database import initialize_db, get_mongo_client, get_mongo_db, schedule_reconnect, get_users_collection
    
    # Intentar establecer la conexión inicial
    if initialize_db(app):
        app.logger.info("Conexión a MongoDB establecida correctamente mediante el módulo database.py")
        client = get_mongo_client()
        db = get_mongo_db()
        # AÑADIDO: Hacer la colección de usuarios accesible desde current_app
        app.users_collection = get_users_collection()
        # AÑADIDO: Hacer la colección de hojas de cálculo accesible desde current_app
        if db is not None:
            app.spreadsheets_collection = db['spreadsheets']
        else:
            app.spreadsheets_collection = None
    else:
        app.logger.warning("No se pudo establecer la conexión inicial a MongoDB, se programará reconexión automática")
        client = None
        db = None
        app.users_collection = None
        app.spreadsheets_collection = None
        # Programamos un intento de reconexión en segundo plano
        schedule_reconnect(delay=30, app=app)
    
    # Inicializar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Configurar el cargador de usuarios para Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None:
            return None
        # Protección defensiva: si la colección no está inicializada, lanza excepción clara
        if not hasattr(app, 'users_collection') or app.users_collection is None:
            app.logger.error("[CRÍTICO] users_collection no está inicializada. Verifica la conexión a MongoDB antes de autenticar usuarios.")
            raise Exception("users_collection no está inicializada. No se puede autenticar usuarios sin conexión a la base de datos.")
        user_data = app.users_collection.find_one({"email": user_id})
        if not user_data:
            return None
        return User(user_data)
    
    # Inicializar filtros personalizados
    init_filters(app)
    
    # Inicializar extensiones
    from app.extensions import init_extensions
    init_extensions(app)
    
    # Configurar logging
    setup_logging(app)
    
    # Registrar blueprints principales primero
    blueprints = [
        (main_bp, ''),
        (auth_bp, ''),
        (catalogs_bp, '/catalogs'),
        (image_bp, '/images'),
        (usuarios_bp, '/usuarios'),
        (errors_bp, '')
    ]
    
    # Registrar blueprints de administración después
    # Registro de blueprints de administración (sin duplicados)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_logs_bp, url_prefix='/admin')
    app.register_blueprint(scripts_bp)
    app.register_blueprint(scripts_tools_bp)  # Usa su url_prefix propio

    # Registrar el blueprint de mantenimiento con su propio prefijo
    maintenance_blueprints = [
        (maintenance_bp, '/admin/maintenance')
    ]
    
    # Registrar blueprints principales
    for bp, prefix in blueprints:
        try:
            app.register_blueprint(bp, url_prefix=prefix)
        except Exception as e:
            app.logger.error(f"Error registrando blueprint {bp.name}: {str(e)}")
    # Registrar blueprint de plantilla de desarrollo
    app.register_blueprint(bp_dev_template)

    # ---
    # Error handlers globales para API (devuelven JSON en endpoints tipo /api/ o si se acepta JSON)
    def api_error_handler(error):
        from flask import request, jsonify
        code = getattr(error, 'code', 500)
        message = getattr(error, 'description', str(error))
        # Si es petición a API o acepta JSON
        if request.path.startswith('/api/') or request.is_json or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({
                'status': 'error',
                'message': message
            }), code
        # Si no, deja que el handler por defecto actúe
        return error
    for err_code in [400, 401, 403, 404, 429, 500]:
        app.register_error_handler(err_code, api_error_handler)
    # ---
    # Handler explícito para 404 que renderiza plantilla personalizada
    from flask import render_template
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('error/404.html'), 404

    # Registrar blueprint de test de sesión SOLO en testing o desarrollo
    if app.config.get('TESTING') or app.config.get('ENV') == 'development' or os.environ.get('FLASK_ENV') in ('development', 'testing'):
        try:
            from app.routes.test_session_routes import test_session_bp
            app.register_blueprint(test_session_bp)
            app.logger.info("Blueprint test_session_bp registrado para tests y desarrollo")
        except Exception as e:
            app.logger.error(f"No se pudo registrar test_session_bp: {e}")
    
    
    # Registrar blueprints de mantenimiento
    app.logger.info(f"Registrando blueprints de mantenimiento. Total: {len(maintenance_blueprints)}")
    for bp, prefix in maintenance_blueprints:
        try:
            app.logger.info(f"Registrando blueprint de mantenimiento: name={bp.name}, prefix={prefix}")
            app.register_blueprint(bp, url_prefix=prefix)
            app.logger.info(f"Blueprint de mantenimiento {bp.name} registrado correctamente con prefijo '{prefix}'")
            # Mostrar las rutas registradas para mantenimiento
            app.logger.info("Rutas registradas para mantenimiento:")
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith('maintenance.'):
                    app.logger.info(f"  - {rule.endpoint} -> {rule}")
        except Exception as e:
            app.logger.error(f"Error registrando blueprint de mantenimiento {bp.name}: {str(e)}")

    # Registrar blueprint de emergencia (emergency_bp) sin prefijo
    try:
        app.register_blueprint(emergency_bp)
        app.logger.info("Blueprint de emergencia (emergency_bp) registrado correctamente.")
    except Exception as e:
        app.logger.error(f"Error registrando blueprint de emergencia: {str(e)}")
    
    # Registrar blueprints adicionales si existen
    try:
        from app.routes.admin_routes import register_admin_blueprints
        if not register_admin_blueprints(app):
            app.logger.warning("No se pudieron registrar los blueprints de administración adicionales")
    except ImportError as e:
        app.logger.error(f"Error importando register_admin_blueprints: {str(e)}")
    
    # Registrar blueprint de imágenes subidas para /imagenes_subidas/<filename>
    try:
        app.register_blueprint(images_bp)
        print("DEBUG: uploaded_images_bp registrado en app (ruta /imagenes_subidas/<filename>)")
    except Exception as e:
        print(f"ERROR registrando uploaded_images_bp: {e}")

    # Inicializar sistema de monitoreo
    try:
        from app import monitoring
        monitoring_thread = monitoring.init_app(app, client)
        app.monitoring_enabled = True
        app.logger.info("Sistema de monitoreo inicializado correctamente")
    except Exception as e:
        app.monitoring_enabled = False
        app.logger.error(f"Error al inicializar el sistema de monitoreo: {str(e)}")
    
    # Ruta de test de sesión
    @app.route('/test_session')
    def test_session():
        from flask import session
        session['test'] = 'ok'
        return f"Valor de session['test']: {session.get('test')}"
    
    # Añadir log para depuración de cookies
    @app.before_request
    def log_cookie():
        from flask import request
        
    
    # Log de la cookie enviada en la respuesta
    @app.after_request
    def log_set_cookie(response):
        app.logger.info(f"[COOKIES] Set-Cookie enviada: {response.headers.get('Set-Cookie')}")
        return response
    
    print(f"MONGO_URI usado: {app.config.get('MONGO_URI')}")
    
    # Crear directorio de logs si no existe
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, 'flask_debug.log')

    # Añadir handler para logs en archivo rotativo
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    
    return app

def setup_logging(app):
    # Usar solo logs en consola para evitar problemas de permisos
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Configuramos la aplicación para usar solo logs en consola
    app.logger.setLevel(logging.DEBUG)

    # También logs en consola si se desea
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
