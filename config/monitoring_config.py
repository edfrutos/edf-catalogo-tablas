# Configuración del sistema de monitoreo
# Este archivo permite controlar diferentes aspectos del monitoreo para
# optimizar recursos

# Configuración general del monitoreo
MONITORING_CONFIG = {
    # Habilitar/deshabilitar monitoreo completamente
    "enabled": True,
    # Intervalo entre ciclos de monitoreo (en segundos)
    "cycle_interval": 1800,  # 30 minutos (reducido de 15 minutos)
    # Configuración de verificaciones del sistema
    "system_health": {
        "enabled": True,
        "cpu_interval": 0.05,  # Intervalo para medición de CPU (reducido de 0.1)
        "disk_check_interval": 5400,  # Verificar disco cada 1.5 horas (3 ciclos)
        "cache_update_interval": 3,  # Actualizar caché cada 3 ciclos
        "cpu_threshold": 98,  # Solo alertar si CPU > 98% (aumentado de 95%)
        "memory_threshold": 99,  # Solo alertar si memoria > 99% (aumentado de 98%)
        "disk_threshold": 99,  # Solo alertar si disco > 99% (aumentado de 98%)
    },
    # Configuración de verificación de base de datos
    "database_health": {
        "enabled": True,
        "check_interval": 2,  # Verificar cada 2 ciclos (1 hora)
    },
    # Configuración de verificación de archivos temporales
    "temp_files": {
        "enabled": True,
        "check_interval": 2,  # Verificar cada 2 ciclos (1 hora)
        # Solo alertar si hay más de 500 archivos (aumentado de 100)
        "file_count_threshold": 500,
        # Solo alertar si ocupan más de 500 MB (aumentado de 100 MB)
        "size_threshold_mb": 500,
    },
    # Configuración de limpieza
    "cleanup": {
        "enabled": True,
        "interval_hours": 6,  # Limpieza cada 6 horas
    },
    # Configuración de métricas
    "metrics": {
        "save_interval": 2,  # Guardar métricas cada 2 ciclos
        "alert_interval": 3,  # Enviar alertas cada 3 ciclos
    },
    # Configuración de notificaciones
    "notifications": {
        "enabled": True,
        "email_alerts": True,
        "console_logs": True,
        "max_alerts_per_hour": 5,  # Máximo 5 alertas por hora
    },
}


# Función para obtener configuración
def get_monitoring_config():
    """Retorna la configuración del monitoreo"""
    return MONITORING_CONFIG


# Función para verificar si una funcionalidad está habilitada
def is_monitoring_enabled(feature=None):
    """Verifica si el monitoreo o una funcionalidad específica está habilitada"""
    if not MONITORING_CONFIG["enabled"]:
        return False

    if feature is None:
        return True

    return MONITORING_CONFIG.get(feature, {}).get("enabled", True)


# Función para obtener umbrales
def get_thresholds(feature):
    """Retorna los umbrales para una funcionalidad específica"""
    return MONITORING_CONFIG.get(feature, {})


# Función para obtener intervalos
def get_intervals(feature):
    """Retorna los intervalos para una funcionalidad específica"""
    return MONITORING_CONFIG.get(feature, {})
