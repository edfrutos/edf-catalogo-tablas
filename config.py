# Script: config.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 config.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # Optimizaciones para reducir consumo de recursos

    # Reduce el tiempo de vida de la sesión a 4 horas para liberar recursos más rápido
    PERMANENT_SESSION_LIFETIME = 14400  # 4 horas

    # Clave secreta para sesiones
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-secreta-por-defecto")
    MONGO_URI = os.getenv("MONGO_URI")

    # Configuración de proxy
    PREFERRED_URL_SCHEME = "https"

    # Desactivar protección CSRF en rutas que no la necesitan para reducir overhead
    WTF_CSRF_CHECK_DEFAULT = (
        False  # Verificar CSRF solo cuando se solicita explícitamente
    )

    # Comprimir respuestas para reducir ancho de banda
    COMPRESS_MIMETYPES = [
        "text/html",
        "text/css",
        "text/xml",
        "application/json",
        "application/javascript",
    ]
    COMPRESS_LEVEL = 6  # Balance entre CPU y nivel de compresión (1-9)
    COMPRESS_MIN_SIZE = 500  # Solo comprimir respuestas mayores a 500 bytes

    # La configuración de sesión se maneja en app.py

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

    # Email
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

    # Flask debug - desactivado en producción para ahorrar recursos
    DEBUG = False  # Forzar a False en producción
    TESTING = False
    EXPLAIN_TEMPLATE_LOADING = False  # Desactivar debugging de plantillas

    # Optimizaciones de caché y rendimiento
    SEND_FILE_MAX_AGE_DEFAULT = 43200  # 12 horas de caché en estáticos

    # Optimizaciones de Jinja para rendimiento
    TEMPLATES_AUTO_RELOAD = False  # Desactivar recarga automática en producción

    # Sesión optimizada
    SESSION_COOKIE_SECURE = True  # Activar en producción
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = None

    # Limitar tamaño de subidas para evitar ataques DoS
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB límite máximo
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app/static/uploads")

    # Configuración adicional que no necesita entrar en app.config
    # Optimizada para menor consumo de recursos
    MONGO_CONFIG = {
        "serverSelectionTimeoutMS": 10000,  # Reducido a 10 segundos
        "connectTimeoutMS": 5000,  # Reducido a 5 segundos
        "socketTimeoutMS": 30000,  # Reducido a 30 segundos
        "retryWrites": True,
        "retryReads": True,
        "maxPoolSize": 10,  # Reducido a 10 conexiones máximas
        "minPoolSize": 1,  # Reducido a 1 conexión mínima
        "maxIdleTimeMS": 60000,  # Reducido a 1 minuto
        "waitQueueTimeoutMS": 10000,  # Reducido a 10 segundos
        "appName": "edefrutos2025_app",  # Identificador para monitoring
    }

    COLLECTION_USERS_UNIFIED = "users_unified"
    COLLECTION_USERS = "users"
    COLLECTION_LOGIN_ATTEMPTS = "login_attempts"
    COLLECTION_RESET_TOKENS = "reset_tokens"
    COLLECTION_AUDIT_LOGS = "audit_logs"
    COLLECTION_CATALOGOS = "catalogos"

    # Ajuste de parámetros de reintentos para ser más eficientes
    MAX_RETRIES = 2  # Reducido de 3 a 2 reintentos
    RETRY_DELAY = 3  # Reducido de 5 a 3 segundos
    MAX_UPLOAD_SIZE = 5  # Tamaño máximo de subida en MB
    LOG_ROTATION_SIZE = 2  # Tamaño en MB para rotación de logs
    LOG_BACKUP_COUNT = 3  # Número de copias de logs a mantener

    # Sesión optimizada
    SESSION_TYPE = "filesystem"  # Eliminado para forzar sesiones solo en cookie
    SESSION_PERMANENT = False
    USE_S3 = os.getenv("USE_S3", "false").lower() in ["true", "1"]
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "app/static/uploads")
    )
    LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"
    SESSION_COOKIE_SECURE = False
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", os.path.join(BaseConfig.BASE_DIR, "app/static/uploads")
    )
    LOG_DIR = os.getenv("LOG_DIR", os.path.join(BaseConfig.BASE_DIR, "logs"))


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = True
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", os.path.join(BaseConfig.BASE_DIR, "app/static/uploads")
    )
    LOG_DIR = os.getenv("LOG_DIR", "/logs")


def get_config():
    env = os.getenv("FLASK_ENV", "production")
    if env == "development":
        return DevelopmentConfig
    return ProductionConfig


Config = get_config()

LOG_ROTATION_SIZE = BaseConfig.LOG_ROTATION_SIZE
LOG_BACKUP_COUNT = BaseConfig.LOG_BACKUP_COUNT

MONGO_CONFIG = BaseConfig.MONGO_CONFIG
COLLECTION_USERS = BaseConfig.COLLECTION_USERS
COLLECTION_CATALOGOS = BaseConfig.COLLECTION_CATALOGOS
COLLECTION_RESET_TOKENS = BaseConfig.COLLECTION_RESET_TOKENS
COLLECTION_AUDIT_LOGS = BaseConfig.COLLECTION_AUDIT_LOGS
