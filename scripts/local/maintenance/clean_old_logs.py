#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpiar archivos de logs antiguos.

Este script busca y elimina archivos de logs que superen un cierto
tiempo de retención configurable.

Uso:
    python clean_old_logs.py [--days 30] [--dry-run] [--log-dir /ruta/a/logs]

Opciones:
    --days N      Número de días de retención (por defecto: 30)
    --dry-run     Solo muestra qué archivos se eliminarían sin borrarlos
    --log-dir     Directorio donde se encuentran los logs (por defecto: ./logs)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuración por defecto
DEFAULT_RETENTION_DAYS = 30
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class LogCleaner:
    """Clase para manejar la limpieza de logs antiguos."""
    
    def __init__(self, log_dir, retention_days=None, dry_run=False, start_datetime=None, end_datetime=None):
        """Inicializa el limpiador de logs.
        
        Args:
            log_dir (str): Directorio donde se encuentran los logs
            retention_days (int): Días de retención para los logs
            dry_run (bool): Si es True, solo muestra qué se haría sin hacer cambios
            start_datetime (datetime): Fecha/hora inicio (opcional)
            end_datetime (datetime): Fecha/hora fin (opcional)
        """
        self.log_dir = Path(log_dir).resolve()
        self.retention_days = retention_days
        self.dry_run = dry_run
        self.logger = self._setup_logging()
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        if start_datetime and end_datetime:
            self.start_ts = start_datetime.timestamp()
            self.end_ts = end_datetime.timestamp()
        elif retention_days is not None:
            self.cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        else:
            self.cutoff_time = None

    def _setup_logging(self):
        """Configura el sistema de logging."""
        logger = logging.getLogger('log_cleaner')
        logger.setLevel(logging.INFO)
        
        # Evitar múltiples handlers si ya están configurados
        if not logger.handlers:
            formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Handler para archivo
            log_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'logs',
                f'clean_logs_{datetime.now().strftime("%Y%m%d")}.log'
            )
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def clean_old_logs(self):
        """Elimina archivos de logs antiguos o en rango de fechas/hora."""
        if not self.log_dir.exists():
            self.logger.error(f"El directorio de logs no existe: {self.log_dir}")
            return False
        
        self.logger.info(f"Iniciando limpieza de logs en: {self.log_dir}")
        if self.start_datetime and self.end_datetime:
            self.logger.info(f"Eliminando logs entre {self.start_datetime} y {self.end_datetime}")
        elif self.retention_days is not None:
            self.logger.info(f"Eliminando logs con más de {self.retention_days} días de antigüedad")
        else:
            self.logger.info(f"No se especificó criterio de limpieza válido.")
            return False
        
        # Patrones de archivos de log a limpiar
        log_patterns = ['*.log', '*.log.*']
        deleted_files = 0
        total_size = 0
        
        try:
            for pattern in log_patterns:
                for log_file in self.log_dir.glob(pattern):
                    # No eliminar archivos de log actuales
                    if log_file.name.startswith('clean_logs_'):
                        continue
                    try:
                        file_mtime = log_file.stat().st_mtime
                        file_size = log_file.stat().st_size
                        borrar = False
                        if self.start_datetime and self.end_datetime:
                            if self.start_ts <= file_mtime <= self.end_ts:
                                borrar = True
                        elif self.cutoff_time is not None:
                            if file_mtime < self.cutoff_time:
                                borrar = True
                        if borrar:
                            if self.dry_run:
                                self.logger.info(f"[DRY RUN] Se eliminaría: {log_file} (Última modificación: {datetime.fromtimestamp(file_mtime)})")
                            else:
                                log_file.unlink()
                                deleted_files += 1
                                total_size += file_size
                                self.logger.info(f"Eliminado: {log_file} (Última modificación: {datetime.fromtimestamp(file_mtime)})")
                    except Exception as e:
                        self.logger.error(f"Error al procesar {log_file}: {str(e)}")
            # Resumen
            self.logger.info(f"Proceso completado. Archivos eliminados: {deleted_files}, Espacio liberado: {self._format_size(total_size)}")
            return True
        except Exception as e:
            self.logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _format_size(size_bytes):
        """Formatea el tamaño en bytes a una cadena legible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"

def parse_arguments():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Limpia archivos de logs antiguos.')
    parser.add_argument('--days', type=int, default=DEFAULT_RETENTION_DAYS,
                        help=f'Número de días de retención (por defecto: {DEFAULT_RETENTION_DAYS})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra qué archivos se eliminarían sin borrarlos')
    parser.add_argument('--log-dir', type=str, default=DEFAULT_LOG_DIR,
                        help=f'Directorio donde se encuentran los logs (por defecto: {DEFAULT_LOG_DIR})')
    return parser.parse_args()

def main():
    """Función principal."""
    args = parse_arguments()
    
    try:
        cleaner = LogCleaner(
            log_dir=args.log_dir,
            retention_days=args.days,
            dry_run=args.dry_run
        )
        
        success = cleaner.clean_old_logs()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
