#!/usr/bin/env python3
# scripts/maintenance/run_maintenance.py

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
MAINTENANCE_LOG_DIR = BASE_DIR / "scripts" / "maintenance" / "logs"


# Configuración de logging
def setup_logging():
    """Configura el sistema de logging para el script de mantenimiento."""
    MAINTENANCE_LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("maintenance")
    logger.setLevel(logging.INFO)

    # Formato del log
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para archivo
    log_file = (
        MAINTENANCE_LOG_DIR / f"maintenance_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Añadir handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def clean_old_logs(logger, days=30):
    """Limpia los logs antiguos."""
    from scripts.maintenance.clean_old_logs import LogCleaner

    logger.info(f"🔍 Iniciando limpieza de logs (retención: {days} días)")
    cleaner = LogCleaner(log_dir=str(LOG_DIR), retention_days=days, dry_run=False)
    return cleaner.clean_old_logs()


def check_disk_usage(logger):
    """Verifica el uso del disco."""
    import shutil

    total, used, free = shutil.disk_usage("/")
    logger.info(f"💾 Uso de disco: {used // (2**30)}GB usados de {total // (2**30)}GB")
    return {
        "total_gb": total // (2**30),
        "used_gb": used // (2**30),
        "free_gb": free // (2**30),
    }


def check_mongodb_connection(logger):
    """Verifica la conexión a MongoDB."""
    try:
        from pymongo import MongoClient

        # Intenta obtener MONGO_URI desde config.py o variables de entorno
        mongo_uri = None
        try:
            from config import MONGO_URI  # type: ignore

            mongo_uri = MONGO_URI
        except ImportError:
            mongo_uri = os.environ.get("MONGO_URI")
            if not mongo_uri:
                logger.error(
                    "❌ No se pudo encontrar MONGO_URI en config.py ni en variables de entorno"
                )
                return False

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Forza la conexión
        logger.info("✅ Conexión a MongoDB exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Script de mantenimiento para EDF Catálogo Tablas"
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Días de retención para logs"
    )
    parser.add_argument(
        "--start-datetime",
        type=str,
        help="Fecha/hora inicio (ISO 8601) para limpieza de logs",
    )
    parser.add_argument(
        "--end-datetime",
        type=str,
        help="Fecha/hora fin (ISO 8601) para limpieza de logs",
    )
    parser.add_argument(
        "--task",
        choices=["all", "logs", "disk", "mongo"],
        default="all",
        help="Tarea específica a ejecutar",
    )

    args = parser.parse_args()
    logger = setup_logging()

    logger.info("=" * 50)
    logger.info("🚀 INICIANDO TAREAS DE MANTENIMIENTO")
    logger.info("=" * 50)

    try:
        if args.task in ["all", "logs"]:
            # Si se pasan start/end, usar rango
            if args.start_datetime and args.end_datetime:
                from scripts.maintenance.clean_old_logs import LogCleaner
                from datetime import datetime

                dt_start = datetime.fromisoformat(args.start_datetime)
                dt_end = datetime.fromisoformat(args.end_datetime)
                logger.info(f"🔍 Limpiando logs entre {dt_start} y {dt_end}")
                cleaner = LogCleaner(
                    log_dir=str(LOG_DIR),
                    retention_days=None,
                    dry_run=False,
                    start_datetime=dt_start,
                    end_datetime=dt_end,
                )
                cleaner.clean_old_logs()
            else:
                clean_old_logs(logger, args.days)

        if args.task in ["all", "disk"]:
            import platform
            import getpass
            import psutil
            import json
            import time

            # System info
            system_info = {
                "sistema_operativo": platform.system() + " " + platform.release(),
                "arquitectura": platform.machine(),
                "usuario": getpass.getuser(),
                "hora_actual": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            # CPU
            cpu_info = {
                "uso_porcentual": psutil.cpu_percent(interval=0.5),
                "nucleos": psutil.cpu_count(logical=True),
            }
            # Memoria
            vmem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            memoria_info = {
                "uso_porcentual": vmem.percent,
                "total_gb": round(vmem.total / (1024**3), 2),
                "disponible_gb": round(vmem.available / (1024**3), 2),
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_usado_gb": round(swap.used / (1024**3), 2),
            }
            # Disco
            du = psutil.disk_usage("/")
            disco_info = {
                "uso_porcentual": du.percent,
                "total_gb": round(du.total / (1024**3), 2),
                "usado_gb": round(du.used / (1024**3), 2),
                "libre_gb": round(du.free / (1024**3), 2),
            }
            output = {
                "system": system_info,
                "cpu": cpu_info,
                "memoria": memoria_info,
                "disco": disco_info,
            }
            print(json.dumps(output))

        if args.task in ["all", "mongo"]:
            check_mongodb_connection(logger)

    except Exception as e:
        logger.error(f"❌ Error durante el mantenimiento: {str(e)}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("🏁 MANTENIMIENTO COMPLETADO")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
