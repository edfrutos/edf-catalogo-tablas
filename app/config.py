import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class BaseConfig:
    """Configuración base común para todos los entornos"""

    # Configuración general de Flask
    SECRET_KEY = os.getenv(
        "SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "dev_key_change_in_production")
    )

    # Configuración de MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGODB_SETTINGS = {
        "connect": False,
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 5000,
        "socketTimeoutMS": 30000,
        "retryWrites": True,
        "retryReads": True,
        "maxPoolSize": 10,
        "minPoolSize": 1,
        "maxIdleTimeMS": 60000,
        "waitQueueTimeoutMS": 10000,
        "appName": "edefrutos2025_app",
    }

    # Configuración de correo electrónico
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        os.getenv("MAIL_DEFAULT_SENDER_NAME"),
        os.getenv("MAIL_DEFAULT_SENDER_EMAIL"),
    )
    MAIL_DEBUG = os.getenv("MAIL_DEBUG", "False") == "True"

    # ===== CONFIGURACIÓN DE SESIONES UNIFICADA =====
    # Configuración centralizada y optimizada de sesiones
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)  # 4 horas de duración
    SESSION_COOKIE_NAME = "edefrutos2025_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_USE_SIGNER = False  # Simplificado para mejor rendimiento
    # SESSION_FILE_DIR se configurará dinámicamente en cada entorno

    # Configuración de AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    USE_S3 = os.getenv("USE_S3", "false").lower() in ["true", "1"]

    # Configuración de seguridad
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB límite máximo
    WTF_CSRF_CHECK_DEFAULT = False  # Configurar según necesidades

    # Rutas de carpetas internas
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "static/uploads"
    )  # Corregido: app/static/uploads
    SPREADSHEET_FOLDER = os.path.join(BASE_DIR, "../spreadsheets")
    LOG_DIR = os.path.join(BASE_DIR, "../logs")


class DevelopmentConfig(BaseConfig):
    """Configuración para entorno de desarrollo"""

    DEBUG = True
    ENV = "development"
    SESSION_COOKIE_SECURE = False  # HTTP permitido en desarrollo
    SESSION_FILE_DIR = os.path.join(BaseConfig.BASE_DIR, "../flask_session")


class ProductionConfig(BaseConfig):
    """Configuración para entorno de producción"""

    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = True  # Solo HTTPS en producción
    SESSION_FILE_DIR = "/tmp/flask_session"  # Directorio temporal en producción

    # Optimizaciones adicionales para producción
    SEND_FILE_MAX_AGE_DEFAULT = 43200  # 12 horas de caché
    TEMPLATES_AUTO_RELOAD = False


class TestingConfig(BaseConfig):
    """Configuración para entorno de testing"""

    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    SESSION_FILE_DIR = os.path.join(BaseConfig.BASE_DIR, "../test_sessions")


def get_config():
    """Obtiene la configuración apropiada según el entorno"""
    env = os.getenv("FLASK_ENV", "production")
    if env == "development":
        return DevelopmentConfig
    elif env == "testing":
        return TestingConfig
    return ProductionConfig


# Configuración por defecto
Config = get_config()
