# app/logging_config.py

import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_ROTATION_SIZE, LOG_BACKUP_COUNT

def setup_logging(app):
    """Configuración optimizada de logs para reducir el consumo de recursos"""
    # Crear directorio de logs si no existe
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar el handler para rotación de logs (tamaño en MB)
    log_file = os.path.join(log_dir, 'app.log')
    max_bytes = LOG_ROTATION_SIZE * 1024 * 1024
    backup_count = LOG_BACKUP_COUNT
    
    # Usar RotatingFileHandler para limitar el tamaño de logs
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    # Formato optimizado para reducir el tamaño del log
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    # Establecer nivel de log a ERROR para reducir verbosidad
    handler.setLevel(logging.ERROR)
    
    # Configurar el logger de la aplicación
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.ERROR)
    
    # En modo DEBUG, mostrar solo mensajes IMPORTANTES (WARNING o superior)
    if app.config.get('DEBUG'):
        app.logger.setLevel(logging.WARNING)
        handler.setLevel(logging.WARNING)
    
    # Deshabilitar logs de dependencias
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('pymongo').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('boto3').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    
    # Configurar manejo de excepciones para mensajes de error graves
    # Esto asegura que los errores críticos se registren siempre
    def handle_exception(exc_type, exc_value, exc_traceback):
        app.logger.error(
            f"Excepción no capturada: {exc_type.__name__}: {exc_value}", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    # Registrar el handler de excepciones
    if not app.config.get('DEBUG'):
        import sys
        sys.excepthook = handle_exception
    
    app.logger.warning("Sistema de logs optimizado iniciado correctamente.")
