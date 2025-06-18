# app/extensions.py

from flask_pymongo import PyMongo
from flask_mail import Mail
import boto3
import certifi

mail = Mail()
mongo = PyMongo()
s3_client = None
catalog_collection = None

def init_extensions(app):
    global s3_client
    global catalog_collection

    # Hacer que la conexión a MongoDB sea opcional
    if app.config.get('MONGO_URI'):
        try:
            # Forzar el uso de certifi para los certificados
            mongo.init_app(app, tlsCAFile=certifi.where())
            catalog_collection = mongo.db.catalogo_tablas
            
        except Exception as e:
            app.logger.error(f"Error al inicializar MongoDB: {e}")
            app.logger.warning("Continuando sin MongoDB - algunas funcionalidades estarán limitadas")
    else:
        app.logger.warning("MONGO_URI no configurado - continuando sin MongoDB")
    
    mail.init_app(app)

    if app.config.get("USE_S3"):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=app.config['AWS_REGION']
        )

    # La asignación de catalog_collection se hace en el bloque try arriba

def is_mongo_available():
    try:
        # Verifica si mongo está inicializado y la conexión es válida
        if mongo is None or not hasattr(mongo, 'db') or mongo.db is None:
            return False
        # Intentar un ping simple
        mongo.cx.admin.command('ping')
        return True
    except Exception:
        return False

