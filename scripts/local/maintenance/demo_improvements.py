#!/usr/bin/env python3
"""
Script de demostración de las mejoras implementadas en el sistema de mantenimiento.
Muestra el uso del wrapper, configuración centralizada y monitoreo mejorado.
"""

import sys
import logging
from pathlib import Path

# Configurar path para importaciones
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar las nuevas utilidades
try:
    from config import config
    from monitoring_utils import SystemMonitor, LogAnalyzer, setup_monitoring_logger
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print(
        f"💡 Asegúrate de que los archivos config.py y monitoring_utils.py estén en el directorio:"
    )
    print(f"   {current_dir}")
    sys.exit(1)


def demo_configuration():
    """Demuestra la configuración centralizada."""
    print("🔧 DEMOSTRACIÓN DE CONFIGURACIÓN CENTRALIZADA")
    print("=" * 50)

    print(f"📁 Directorio raíz del proyecto: {config.PROJECT_ROOT}")
    print(f"📁 Directorio de scripts: {config.SCRIPTS_DIR}")
    print(f"📁 Directorio de logs: {config.LOGS_DIR}")
    print(f"📁 Directorio de logs de mantenimiento: {config.MAINTENANCE_LOGS_DIR}")
    print(f"📁 Directorio de backup: {config.BACKUP_DIR}")
    print(f"📁 Directorio de imágenes: {config.UPLOAD_FOLDER}")

    print(f"\n⚙️ Configuración de MongoDB:")
    print(f"   URI: {config.MONGO_URI[:50]}...")
    print(f"   Base de datos: {config.MONGODB_DB}")

    print(f"\n📧 Configuración de correo:")
    print(f"   Envío habilitado: {config.SEND_EMAIL}")
    print(f"   Servidor: {config.EMAIL_SERVER}")
    print(f"   Puerto: {config.EMAIL_PORT}")

    print(f"\n🔍 Configuración de monitoreo:")
    print(f"   Umbral de disco: {config.DISK_USAGE_THRESHOLD}%")
    print(f"   Umbral de memoria: {config.MEMORY_USAGE_THRESHOLD}%")
    print(f"   Modo de limpieza: {config.CLEANUP_MODE}")


def demo_monitoring():
    """Demuestra el sistema de monitoreo mejorado."""
    print("\n📊 DEMOSTRACIÓN DE MONITOREO MEJORADO")
    print("=" * 50)

    # Configurar logger
    logger = setup_monitoring_logger("demo")

    # Crear monitor del sistema
    monitor = SystemMonitor(logger)

    print("🔍 Recopilando métricas del sistema...")
    metrics = monitor.collect_system_metrics()

    if metrics:
        print("✅ Métricas recopiladas exitosamente")
        print(f"   CPU: {metrics.get('cpu', {}).get('usage_percent', 0)}%")
        print(f"   Memoria: {metrics.get('memory', {}).get('usage_percent', 0)}%")
        print(f"   Disco: {metrics.get('disk', {}).get('usage_percent', 0)}%")

        # Verificar alertas
        alerts = monitor.check_alerts()
        if alerts:
            print("\n🚨 Alertas detectadas:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print("\n✅ No hay alertas activas")

        # Guardar métricas
        metrics_file = monitor.save_metrics()
        if metrics_file:
            print(f"💾 Métricas guardadas en: {metrics_file}")
    else:
        print("❌ Error recopilando métricas")


def demo_log_analysis():
    """Demuestra el análisis de logs."""
    print("\n📋 DEMOSTRACIÓN DE ANÁLISIS DE LOGS")
    print("=" * 50)

    logger = setup_monitoring_logger("demo")
    analyzer = LogAnalyzer(logger)

    # Buscar archivos de log recientes
    log_files = list(config.MAINTENANCE_LOGS_DIR.glob("*.log"))

    if log_files:
        # Analizar el log más reciente
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        print(f"📄 Analizando log: {latest_log.name}")

        analysis = analyzer.analyze_log_file(latest_log, hours=24)

        if "error" not in analysis:
            print(f"   📊 Total de líneas: {analysis.get('total_lines', 0)}")
            print(f"   ❌ Errores: {analysis.get('errors', 0)}")
            print(f"   ⚠️ Advertencias: {analysis.get('warnings', 0)}")
            print(f"   ℹ️ Información: {analysis.get('info', 0)}")

            recent_errors = analysis.get("recent_errors", [])
            if recent_errors:
                print(f"\n🔍 Últimos errores:")
                for error in recent_errors[-3:]:  # Mostrar solo los últimos 3
                    print(f"   {error}")
        else:
            print(f"❌ Error analizando log: {analysis['error']}")
    else:
        print("📄 No se encontraron archivos de log para analizar")


def demo_wrapper_usage():
    """Demuestra el uso del wrapper."""
    print("\n🚀 DEMOSTRACIÓN DEL WRAPPER")
    print("=" * 50)

    print("El wrapper permite ejecutar scripts desde cualquier directorio:")
    print()
    print("📝 Uso básico:")
    print("   python maintenance_wrapper.py run_maintenance.py --task disk")
    print("   python maintenance_wrapper.py clean_images_scheduled.py")
    print("   python maintenance_wrapper.py 10_backup_incremental.py")
    print()
    print("✨ Beneficios:")
    print("   ✅ Maneja automáticamente las rutas")
    print("   ✅ Carga variables de entorno")
    print("   ✅ Configura el entorno Python")
    print("   ✅ Ejecuta desde cualquier directorio")
    print("   ✅ Captura y muestra errores claramente")


def main():
    """Función principal de demostración."""
    print("🎯 DEMOSTRACIÓN DE MEJORAS EN EL SISTEMA DE MANTENIMIENTO")
    print("=" * 60)

    # Configurar el entorno
    config.setup_environment()

    try:
        # Demostrar cada mejora
        demo_configuration()
        demo_monitoring()
        demo_log_analysis()
        demo_wrapper_usage()

        print("\n" + "=" * 60)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("\n📚 Resumen de mejoras implementadas:")
        print("   1. 🔧 Configuración centralizada (config.py)")
        print("   2. 🚀 Wrapper para ejecución desde cualquier directorio")
        print("   3. 📊 Sistema de monitoreo con alertas")
        print("   4. 📋 Análisis automático de logs")
        print("   5. 📧 Notificaciones por correo")
        print("   6. 💾 Guardado de métricas en JSON")

    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
