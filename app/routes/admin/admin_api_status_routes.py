# Script: admin_api_status_routes.py
# Descripción: Rutas API administrativas de estado, caché y pruebas.
# Autor: EDF Developer

import logging
from datetime import datetime

from flask import current_app, jsonify

from app.cache_system import get_cache_stats
from app.database import get_mongo_db
from app.decorators import admin_required
from app.routes.admin.admin_system import get_system_status_data

logger = logging.getLogger(__name__)


def register_admin_api_status_routes(admin_bp) -> None:
    """Registra rutas API administrativas de estado sobre el blueprint admin."""

    @admin_bp.route("/api/system-status")
    @admin_required
    def api_system_status():
        """API endpoint para obtener el estado del sistema en tiempo real"""
        try:
            from app.monitoring import check_system_health

            # Forzar actualización inmediata del estado del sistema
            check_system_health()

            # Obtener datos actualizados
            data = get_system_status_data()

            # Reestructurar datos para que coincidan con lo que espera el JavaScript
            system_metrics = (
                data.get("health", {}).get("metrics", {}).get("system_status", {})
            )

            # Validar que tenemos datos válidos
            if not system_metrics or system_metrics.get("cpu_usage", 0) == 0:
                # Si no hay datos, intentar obtenerlos directamente
                import psutil

                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                cpu_usage = psutil.cpu_percent(interval=0.1)

                system_metrics = {
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

            response_data = {"system_status": system_metrics}

            current_app.logger.info(f"API system-status devolviendo: {response_data}")
            return jsonify({"status": "success", "data": response_data})

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            logger.error(f"Error en api_system_status: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {"status": "error", "message": "Error al obtener estado del sistema"}
                ),
                500,
            )


    @admin_bp.route("/api/drive-backups")
    @admin_required
    def api_drive_backups():
        """API para obtener la lista de respaldos en Google Drive"""
        try:
            db = get_mongo_db()
            if db is None:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "No se pudo conectar a la base de datos",
                        }
                    ),
                    500,
                )

            # Obtener respaldos de la base de datos
            backups = list(db.backups.find({}, {"_id": 0}).sort("uploaded_at", -1))

            # Convertir ObjectId a string si existe
            for backup in backups:
                if "uploaded_at" in backup:
                    backup["uploaded_at"] = backup["uploaded_at"].isoformat()

            return jsonify({"success": True, "backups": backups, "count": len(backups)})

        except Exception as e:
            current_app.logger.error(f"Error al obtener respaldos de Drive: {str(e)}")
            return jsonify({"success": False, "error": f"Error interno: {str(e)}"}), 500


    @admin_bp.route("/api/cache-stats")
    @admin_required
    def api_cache_stats():
        """API endpoint para obtener las estadísticas del caché en tiempo real"""
        try:
            cache_stats = get_cache_stats()
            return jsonify({"status": "success", "data": cache_stats})

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en api_cache_stats: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Error al obtener estadísticas del caché",
                    }
                ),
                500,
            )


    @admin_bp.route("/api/test-cache")
    @admin_required
    def test_cache():
        """Endpoint temporal para generar actividad en el caché y probar las estadísticas"""
        import random

        from app.cache_system import get_cache, set_cache

        try:
            # Generar algunas operaciones de caché para pruebas
            test_keys = [f"test_key_{i}" for i in range(5)]

            for key in test_keys:
                # Intentar obtener valor (generará miss si no existe)
                value = get_cache(key)

                if value is None:
                    # Si no existe, crear uno nuevo
                    set_cache(key, f"test_value_{random.randint(1, 100)}", ttl=300)

            # Hacer algunas consultas adicionales para generar hits
            for _i in range(3):
                get_cache(f"test_key_{random.randint(0, 4)}")

            cache_stats = get_cache_stats()
            return jsonify(
                {
                    "status": "success",
                    "message": "Actividad de caché generada correctamente",
                    "data": cache_stats,
                }
            )

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en test_cache: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {"status": "error", "message": "Error al generar actividad del caché"}
                ),
                500,
            )


    @admin_bp.route("/api/test-database")
    @admin_required
    def test_database():
        """Endpoint para probar la conexión de base de datos manualmente"""
        try:
            from app import monitoring
            from app.database import get_mongo_client

            # Intentar obtener cliente y verificar conexión
            client = get_mongo_client()
            success = monitoring.check_database_health(client)  # type: ignore

            database_status = monitoring._app_metrics.get(
                "database_status",
                {
                    "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_available": False,
                    "response_time_ms": 0,
                    "error": "No se pudo verificar el estado",
                },
            )

            return jsonify(
                {
                    "status": "success",
                    "message": "Verificación de base de datos completada",
                    "data": database_status,
                }
            )

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            logger.error(f"Error en test_database: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Error al verificar la base de datos",
                        "data": {
                            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "is_available": False,
                            "response_time_ms": 0,
                            "error": str(e),
                        },
                    }
                ),
                500,
            )
