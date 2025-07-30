# app/extensions.py

from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_login import LoginManager
from flask_session import Session
import boto3
import certifi
import logging
import os
import sys

mail = Mail()
mongo = PyMongo()
login_manager = LoginManager()
session_handler = Session()  # Inicializar Flask-Session
s3_client = None
catalog_collection = None

# Configurar logging
logger = logging.getLogger("extensions")


def init_extensions(app):
    global s3_client
    global catalog_collection
    
    logger.info("Inicializando extensiones...")
    
    # Configurar Flask-Session primero
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "edf_catalogo:"
    
    # Asegurarse de que el directorio de sesiones existe
    if getattr(sys, "frozen", False):
        session_dir = os.path.join(os.path.dirname(sys.executable), "flask_session")
    else:
        session_dir = os.path.join(
            app.config.get("BASE_DIR", os.getcwd()), "flask_session"
        )
    
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    app.config["SESSION_FILE_DIR"] = session_dir
    logger.info(f"Directorio de sesiones: {session_dir}")
    
    # Inicializar Flask-Session
    session_handler.init_app(app)
    logger.info("Flask-Session inicializado")
    
    # Inicializar Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.login_message_category = "warning"
    logger.info("Flask-Login inicializado")
    
    # Definir la función de carga de usuario para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User

        user = User.get_by_id(user_id)
        logger.info(
            f"Cargando usuario: {user_id}, Resultado: {'Encontrado' if user else 'No encontrado'}"
        )
        return user

    # Hacer que la conexión a MongoDB sea opcional
    if app.config.get("MONGO_URI"):
        try:
            # Forzar el uso de certifi para los certificados
            mongo.init_app(app, tlsCAFile=certifi.where())
            catalog_collection = mongo.db.get_collection("catalogo_tablas")  # type: ignore
            
        except Exception as e:
            app.logger.error(f"Error al inicializar MongoDB: {e}")
            app.logger.warning(
                "Continuando sin MongoDB - algunas funcionalidades estarán limitadas"
            )
    else:
        app.logger.warning("MONGO_URI no configurado - continuando sin MongoDB")
    
    mail.init_app(app)
    logger.info("Flask-Mail inicializado")

    if app.config.get("USE_S3"):
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"],
            region_name=app.config["AWS_REGION"],
        )

    # La asignación de catalog_collection se hace en el bloque try arriba


def is_mongo_available():
    try:
        # Verifica si mongo está inicializado y la conexión es válida
        if mongo is None or not hasattr(mongo, "db") or mongo.db is None:
            return False
        # Intentar un ping simple
        mongo.cx.admin.command("ping")  # type: ignore
        return True
    except Exception:
        return False
