# Script: monitoring.py
# Descripción: [Sistema de monitoreo para la aplicación Este módulo proporciona herramientas para monitorear la salud de la aplicación y generar alertas cuando se detectan problemas.]
# Uso: python3 monitoring.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Sistema de monitoreo para la aplicación
Este módulo proporciona herramientas para monitorear la salud de la aplicación
y generar alertas cuando se detectan problemas.
"""

import datetime  # type: ignore
import json
import logging
import os
import threading
import time

import psutil  # type: ignore
from flask import current_app  # noqa: F401

# Importar módulo de notificaciones
from app import notifications

# Configuración de logging
logger = logging.getLogger(__name__)

# Métricas de la aplicación
_app_metrics = {
    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "database_status": {
        "last_checked": None,
        "is_available": False,
        "response_time_ms": 0,
        "error": None,
    },
    "cache_status": {"size": 0, "hit_count": 0, "miss_count": 0, "hit_rate": 0.0},
    "system_status": {
        "cpu_usage": 0,
        "memory_usage": {"percent": 0, "used_mb": 0, "total_mb": 0},
        "disk_usage": {"percent": 0, "used_gb": 0, "total_gb": 0},
    },
    "request_stats": {"total_requests": 0, "error_count": 0, "avg_response_time_ms": 0},
    "temp_files": {"count": 0, "total_size_mb": 0, "files": []},
}

# Ruta para el archivo de métricas (cambiado para evitar problemas de permisos)
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_DIR = os.path.join(APP_ROOT, "app_data")
os.makedirs(METRICS_DIR, exist_ok=True)  # Crear directorio si no existe
_metrics_file = os.path.join(METRICS_DIR, "edefrutos2025_metrics.json")


def save_metrics():
    """Guarda las métricas en un archivo JSON"""
    try:
        with open(_metrics_file, "w") as f:
            json.dump(_app_metrics, f, indent=2)
    except Exception as e:
        logger.error(f"Error al guardar métricas: {str(e)}")


def load_metrics():
    """Carga las métricas desde el archivo JSON si existe"""
    if os.path.exists(_metrics_file):
        try:
            with open(_metrics_file) as f:
                data = json.load(f)
                # Actualizar solo las métricas que se pueden persistir
                for key in ["cache_status", "request_stats"]:
                    if key in data:
                        _app_metrics[key] = data[key]
        except Exception as e:
            logger.error(f"Error al cargar métricas: {str(e)}")


def check_database_health(db_client):
    """Comprueba la salud de la conexión a la base de datos"""
    start_time = time.time()

    # Si no hay cliente, intentar obtener uno nuevo
    if db_client is None:
        try:
            from app.database import get_mongo_client

            db_client = get_mongo_client()
        except Exception as e:
            logger.warning(f"No se pudo obtener cliente de MongoDB: {e}")

    # Si aún no hay cliente, marcar como no disponible
    if db_client is None:
        _app_metrics["database_status"] = {
            "last_checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_available": False,
            "response_time_ms": 0,
            "error": "Cliente de MongoDB no disponible",
        }
        return False

    try:
        # Intenta una operación simple para verificar conectividad
        admin_db = db_client.admin
        admin_db.command("serverStatus")
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # convertir a milisegundos

        _app_metrics["database_status"] = {
            "last_checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_available": True,
            "response_time_ms": round(response_time, 2),
            "error": None,
        }
        return True
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        _app_metrics["database_status"] = {
            "last_checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_available": False,
            "response_time_ms": round(response_time, 2),
            "error": str(e),
        }
        logger.error(f"Error de conexión a la base de datos: {str(e)}")
        return False


def check_system_health():
    """Comprueba la salud del sistema"""
    try:
        # Usar intervalo de 0.1 segundos para obtener medición más precisa
        # Si es la primera vez, psutil necesita un intervalo para medir
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        _app_metrics["system_status"] = {
            "cpu_usage": cpu_usage,
            "memory_usage": {
                "percent": memory.percent,
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "total_mb": round(memory.total / (1024 * 1024), 2),
            },
            "disk_usage": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            },
        }

        # Actualizar métricas de caché
        update_cache_metrics()

        # Verificar si hay condiciones de alerta (umbrales ajustados para reducir alertas innecesarias)
        if cpu_usage > 95:
            logger.warning(f"Alerta: Alto uso de CPU: {cpu_usage}%")
        if memory.percent > 98:
            logger.warning(f"Alerta: Alto uso de memoria: {memory.percent}%")
        if disk.percent > 98:
            logger.warning(f"Alerta: Alto uso de disco: {disk.percent}%")

    except Exception as e:
        logger.error(f"Error al comprobar salud del sistema: {str(e)}")
        # En caso de error, asegurar que system_status tenga una estructura válida
        _app_metrics["system_status"] = {
            "cpu_usage": 0,
            "memory_usage": {"percent": 0, "used_mb": 0, "total_mb": 0},
            "disk_usage": {"percent": 0, "used_gb": 0, "total_gb": 0},
        }


def check_temp_files():
    """Verifica los archivos temporales de la aplicación"""
    try:
        # Comprobar archivos específicos de la aplicación en /tmp/
        app_files = [f for f in os.listdir("/tmp/") if f.startswith("edefrutos2025_")]
        total_size = 0

        for file in app_files:
            file_path = os.path.join("/tmp/", file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)

        _app_metrics["temp_files"] = {
            "count": len(app_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": app_files,
        }

        # Alerta si hay demasiados archivos o si ocupan mucho espacio
        if len(app_files) > 100:
            logger.warning(
                f"Alerta: Hay {len(app_files)} archivos temporales de la aplicación"
            )
        if total_size > 100 * 1024 * 1024:  # 100 MB
            logger.warning(
                f"Alerta: Los archivos temporales ocupan {round(total_size / (1024 * 1024), 2)} MB"
            )

    except Exception as e:
        logger.error(f"Error al comprobar archivos temporales: {str(e)}")


def update_cache_metrics(hit=False, miss=False, size=None):
    """Actualiza las métricas de caché"""
    if hit:
        _app_metrics["cache_status"]["hit_count"] += 1
    if miss:
        _app_metrics["cache_status"]["miss_count"] += 1
    if size is not None:
        _app_metrics["cache_status"]["size"] = size

    # Calcular tasa de aciertos
    total = (
        _app_metrics["cache_status"]["hit_count"]
        + _app_metrics["cache_status"]["miss_count"]
    )
    if total > 0:
        _app_metrics["cache_status"]["hit_rate"] = round(
            _app_metrics["cache_status"]["hit_count"] / total * 100, 2
        )


def record_request(response_time_ms, is_error=False):
    """Registra estadísticas de una solicitud"""
    _app_metrics["request_stats"]["total_requests"] += 1

    if is_error:
        _app_metrics["request_stats"]["error_count"] += 1

    # Actualizar tiempo de respuesta promedio
    current_avg = _app_metrics["request_stats"]["avg_response_time_ms"]
    total_reqs = _app_metrics["request_stats"]["total_requests"]

    if total_reqs > 1:
        new_avg = ((current_avg * (total_reqs - 1)) + response_time_ms) / total_reqs
        _app_metrics["request_stats"]["avg_response_time_ms"] = round(new_avg, 2)
    else:
        _app_metrics["request_stats"]["avg_response_time_ms"] = round(
            response_time_ms, 2
        )


def get_health_status():
    """Devuelve un informe completo del estado de salud del sistema (solo lee métricas ya calculadas)"""
    # NO recalcula métricas costosas aquí
    uptime = datetime.datetime.now() - datetime.datetime.strptime(
        _app_metrics["start_time"], "%Y-%m-%d %H:%M:%S"
    )
    health_report = {
        "status": "healthy",  # Por defecto asumimos que está saludable
        "uptime_seconds": uptime.total_seconds(),
        "uptime_human": str(uptime).split(".")[0],  # Formato HH:MM:SS
        "metrics": _app_metrics,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Determinar el estado general basado en criterios múltiples
    if not _app_metrics["database_status"]["is_available"]:
        health_report["status"] = "degraded"

    # Verificar métricas del sistema de forma segura
    system_status = _app_metrics.get("system_status", {})

    # Manejar el caso donde system_status podría ser un entero en lugar de un diccionario
    if isinstance(system_status, dict):
        cpu_usage = system_status.get("cpu_usage", 0)
        memory_usage = system_status.get("memory_usage", {})

        # Verificar CPU
        if isinstance(cpu_usage, (int, float)) and cpu_usage > 90:
            health_report["status"] = "at_risk"

        # Verificar memoria de forma segura
        if isinstance(memory_usage, dict):
            memory_percent = memory_usage.get("percent", 0)
            if isinstance(memory_percent, (int, float)) and memory_percent > 90:
                health_report["status"] = "at_risk"
        elif isinstance(memory_usage, (int, float)) and memory_usage > 90:
            # Caso donde memory_usage es directamente un número
            health_report["status"] = "at_risk"
    else:
        # Si system_status no es un diccionario, registrar el problema pero no fallar
        logger.warning(
            f"system_status tiene tipo inesperado: {type(system_status)}, valor: {system_status}"
        )

    # Calcular tasa de error
    error_rate = 0
    total_requests = _app_metrics["request_stats"].get("total_requests", 0)
    error_count = _app_metrics["request_stats"].get("error_count", 0)
    if total_requests > 0:
        error_rate = (error_count / total_requests) * 100
    else:
        error_rate = 0
    if error_rate > 10:  # Si más del 10% de las solicitudes fallan
        health_report["status"] = "unhealthy"
    health_report["error_rate"] = error_rate
    return health_report


def cleanup_old_temp_files(
    days=2,
):  # Reducido a 2 días para limpiar archivos temporales más frecuentemente
    """Limpia archivos temporales antiguos"""
    try:
        now = time.time()
        count_removed = 0
        bytes_removed = 0

        for file in os.listdir("/tmp/"):
            if file.startswith("edefrutos2025_"):
                file_path = os.path.join("/tmp/", file)
                if os.path.isfile(file_path):
                    # Comprobar si el archivo es más antiguo que 'days'
                    mtime = os.path.getmtime(file_path)
                    if (now - mtime) > (days * 86400):  # días en segundos
                        # Conservar un registro de los archivos eliminados
                        file_size = os.path.getsize(file_path)
                        try:
                            os.remove(file_path)
                            count_removed += 1
                            bytes_removed += file_size
                            logger.info(f"Archivo temporal antiguo eliminado: {file}")
                        except Exception as e:
                            logger.error(
                                f"Error al eliminar archivo temporal {file}: {str(e)}"
                            )

        if count_removed > 0:
            logger.info(
                f"Limpieza completada: {count_removed} archivos eliminados, "
                f"{round(bytes_removed / (1024 * 1024), 2)} MB liberados"
            )

        return {"files_removed": count_removed, "bytes_removed": bytes_removed}

    except Exception as e:
        logger.error(f"Error en la limpieza de archivos temporales: {str(e)}")
        return {"error": str(e)}


def start_monitoring_thread(app, mongo_client):
    """Inicia un hilo para monitoreo periódico"""

    def monitor_app():
        with app.app_context():
            logger.info("Iniciando hilo de monitoreo")

            # Cargar métricas existentes si las hay
            load_metrics()

            while True:
                try:
                    # Verificar salud de la base de datos
                    check_database_health(mongo_client)

                    # Verificar salud del sistema
                    check_system_health()

                    # Verificar archivos temporales
                    check_temp_files()

                    # Realizar limpieza periódica (cada 6 horas aproximadamente)
                    current_hour = datetime.datetime.now().hour
                    if current_hour % 6 == 0:  # A las 0, 6, 12, 18 horas
                        cleanup_old_temp_files()

                        # Guardar métricas actualizadas
                    save_metrics()

                    # Verificar si hay alertas que enviar
                    try:
                        health_status = get_health_status()
                        notifications.check_and_alert(health_status["metrics"])
                    except Exception as e:
                        logger.error(f"Error al enviar notificaciones: {str(e)}")

                except Exception as e:
                    logger.error(f"Error en el hilo de monitoreo: {str(e)}")

                # Esperar antes del siguiente ciclo (aumentado a 15 minutos para reducir carga)
                time.sleep(900)

    # Crear e iniciar el hilo
    monitor_thread = threading.Thread(target=monitor_app, daemon=True)
    monitor_thread.start()
    return monitor_thread


# Función para integrar con Flask
def init_app(app, mongo_client):
    """Inicializa el sistema de monitoreo con la aplicación Flask"""
    # Inicializar el sistema de notificaciones
    notifications.init_app(app)

    # Iniciar el hilo de monitoreo
    monitor_thread = start_monitoring_thread(app, mongo_client)

    # Registrar las métricas iniciales con validación
    with app.app_context():
        logger.info("Inicializando sistema de monitoreo")

        # Ejecutar verificaciones iniciales múltiples veces para asegurar datos válidos
        try:
            check_system_health()
            check_temp_files()

            # Verificar que las métricas se generaron correctamente
            system_status = _app_metrics.get("system_status", {})
            if system_status and system_status.get("cpu_usage", 0) == 0:
                logger.warning(
                    "Primera verificación no generó datos válidos, reintentando..."
                )
                time.sleep(0.5)
                check_system_health()

            save_metrics()

            # Log con verificación segura
            system_status = _app_metrics.get("system_status", {})
            cpu_usage = system_status.get("cpu_usage", 0) if system_status else 0
            memory_usage = (
                system_status.get("memory_usage", {}) if system_status else {}
            )
            memory_percent = memory_usage.get("percent", 0) if memory_usage else 0

            logger.info(
                f"Métricas iniciales: CPU={cpu_usage}%, Memoria={memory_percent}%"
            )
        except Exception as e:
            logger.error(f"Error en inicialización de métricas: {str(e)}")

    return monitor_thread
