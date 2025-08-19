#!/usr/bin/env python3

# Script: logging_unified.py
# Descripción: [Sistema de logging centralizado y unificado para la aplicación]
# Uso: from app.logging_unified import setup_unified_logging
# Autor: EDF Developer - 2025-01-16


import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class UnifiedLogger:
    """Clase para manejar el logging unificado de la aplicación"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UnifiedLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.loggers = {}
            self.log_dir = None
            self.log_level = logging.INFO
            self._initialized = True

    def setup(
        self, app=None, log_dir: Optional[str] = None, log_level: int = logging.INFO
    ):
        """Configura el sistema de logging unificado"""

        # Determinar directorio de logs
        if log_dir:
            self.log_dir = Path(log_dir)
        elif os.environ.get("LOG_DIR"):
            # Priorizar LOG_DIR de variables de entorno (para aplicaciones empaquetadas)
            self.log_dir = Path(os.environ["LOG_DIR"])
        elif app and hasattr(app, "config") and app.config.get("LOG_DIR"):
            self.log_dir = Path(app.config["LOG_DIR"])
        else:
            # Directorio por defecto - usar ruta relativa para evitar problemas de permisos
            try:
                # Usar directorio del archivo actual para evitar problemas de permisos
                base_dir = Path(__file__).parent.parent
                self.log_dir = base_dir / "logs"
            except Exception:
                # Fallback: usar directorio temporal
                import tempfile

                self.log_dir = Path(tempfile.gettempdir()) / "edf_logs"

        # Crear directorio de logs si no existe
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Si no se puede crear el directorio, usar uno temporal
            import tempfile

            self.log_dir = Path(tempfile.gettempdir()) / "edf_logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_level = log_level

        # Configurar formato unificado
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Configurar handler principal para archivo
        main_log_file = self.log_dir / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file, maxBytes=5 * 1024 * 1024, backupCount=5  # 5MB
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        # Configurar handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Limpiar handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Añadir nuevos handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Configurar loggers específicos para reducir verbosidad
        self._configure_external_loggers()

        # Configurar logger de la aplicación
        if app:
            app.logger.setLevel(log_level)
            # Flask ya tiene sus propios handlers, los mantenemos
            app.logger.info("✅ Sistema de logging unificado inicializado")

        logging.info(f"✅ Logging unificado configurado - Directorio: {self.log_dir}")

        return self

    def _configure_external_loggers(self):
        """Configura loggers de librerías externas para reducir verbosidad"""
        external_loggers = {
            "werkzeug": logging.ERROR,  # Más restrictivo para Werkzeug
            "pymongo": logging.WARNING,
            "urllib3": logging.WARNING,
            "boto3": logging.WARNING,
            "botocore": logging.WARNING,
            "requests": logging.WARNING,
            "flask_session": logging.WARNING,
            "app.routes.error_routes": logging.ERROR,  # Reducir logs de errores 404
            "app.routes.maintenance_routes": logging.WARNING,  # Reducir logs repetitivos
            "extensions": logging.WARNING,  # Reducir logs de carga de usuario
        }

        for logger_name, level in external_loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene un logger específico con configuración unificada"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.log_level)
            self.loggers[name] = logger

        return self.loggers[name]

    def create_module_logger(
        self, module_name: str, log_file: Optional[str] = None
    ) -> logging.Logger:
        """Crea un logger específico para un módulo con archivo propio"""
        logger = logging.getLogger(module_name)
        logger.setLevel(self.log_level)

        if log_file and self.log_dir:
            # Crear handler específico para el módulo
            module_log_file = self.log_dir / log_file
            module_handler = logging.handlers.RotatingFileHandler(
                module_log_file, maxBytes=2 * 1024 * 1024, backupCount=3  # 2MB
            )
            module_handler.setLevel(self.log_level)

            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            module_handler.setFormatter(formatter)

            logger.addHandler(module_handler)

        self.loggers[module_name] = logger
        return logger


# Instancia global del logger unificado
unified_logger = UnifiedLogger()


def setup_unified_logging(
    app=None, log_dir: Optional[str] = None, log_level: int = logging.INFO
):
    """Función principal para configurar el logging unificado"""
    return unified_logger.setup(app, log_dir, log_level)


def get_logger(name: str) -> logging.Logger:
    """Función de conveniencia para obtener un logger"""
    return unified_logger.get_logger(name)


def create_module_logger(
    module_name: str, log_file: Optional[str] = None
) -> logging.Logger:
    """Función de conveniencia para crear un logger de módulo"""
    return unified_logger.create_module_logger(module_name, log_file)


# Configuración por defecto si se ejecuta directamente
if __name__ == "__main__":
    setup_unified_logging()
    logger = get_logger(__name__)
    logger.info("Sistema de logging unificado configurado correctamente")
