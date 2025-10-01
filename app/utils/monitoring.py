#!/usr/bin/env python3
"""
Script para monitoreo del servidor y recursos del sistema.
"""

import os
import platform
import sys
from datetime import datetime

import psutil

# Agregar el directorio raíz al path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)


def get_system_info():
    """Obtener información del sistema"""
    try:
        print("📊 Información del Sistema:")
        print(f"   Sistema Operativo: {platform.system()} {platform.release()}")
        print(f"   Arquitectura: {platform.machine()}")
        print(f"   Procesador: {platform.processor()}")
        print(f"   Versión Python: {platform.python_version()}")

        # Información de memoria
        memory = psutil.virtual_memory()
        print("\n💾 Memoria:")
        print(f"   Total: {memory.total / (1024**3):.1f} GB")
        print(f"   Disponible: {memory.available / (1024**3):.1f} GB")
        print(f"   Usada: {memory.used / (1024**3):.1f} GB ({memory.percent}%)")

        # Información de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        print("\n🖥️ CPU:")
        print(f"   Núcleos: {cpu_count}")
        print(f"   Uso actual: {cpu_percent}%")

        # Información de disco
        disk = psutil.disk_usage("/")
        print("\n💿 Disco:")
        print(f"   Total: {disk.total / (1024**3):.1f} GB")
        print(f"   Usado: {disk.used / (1024**3):.1f} GB")
        print(f"   Libre: {disk.free / (1024**3):.1f} GB")
        print(f"   Porcentaje usado: {disk.percent}%")

        # Información de red
        network = psutil.net_io_counters()
        print("\n🌐 Red:")
        print(f"   Bytes enviados: {network.bytes_sent / (1024**2):.1f} MB")
        print(f"   Bytes recibidos: {network.bytes_recv / (1024**2):.1f} MB")

        # Procesos del sistema
        print("\n🔄 Procesos:")
        print(f"   Total de procesos: {len(psutil.pids())}")

        # Procesos Python
        python_processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                if "python" in proc.info["name"].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"   Procesos Python: {len(python_processes)}")
        for proc in python_processes[:5]:  # Mostrar solo los primeros 5
            print(
                f"     PID {proc['pid']}: {proc['name']} (CPU: {proc['cpu_percent']:.1f}%, Mem: {proc['memory_percent']:.1f}%)"
            )

        return True

    except Exception as e:
        print(f"❌ Error obteniendo información del sistema: {e}")
        return False


def check_application_status():
    """Verificar estado de la aplicación"""
    try:
        print("\n🔍 Estado de la Aplicación:")

        # Verificar directorio de logs
        log_dir = os.path.join(root_dir, "logs")
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
            print(f"   Archivos de log: {len(log_files)}")
        else:
            print("   Archivos de log: No encontrados")

        # Verificar directorio de backups
        backup_dir = os.path.join(root_dir, "backups")
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".json.gz")]
            print(f"   Archivos de backup: {len(backup_files)}")
        else:
            print("   Archivos de backup: No encontrados")

        # Verificar directorio de sesiones
        session_dir = os.path.join(root_dir, "flask_session")
        if os.path.exists(session_dir):
            session_files = [f for f in os.listdir(session_dir)]
            print(f"   Archivos de sesión: {len(session_files)}")
        else:
            print("   Archivos de sesión: No encontrados")

        return True

    except Exception as e:
        print(f"❌ Error verificando estado de la aplicación: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando monitoreo del sistema...")
    print(f"⏰ Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success1 = get_system_info()
    success2 = check_application_status()

    if success1 and success2:
        print("\n✅ Monitoreo completado exitosamente")
        sys.exit(0)
    else:
        print("\n❌ Monitoreo completado con errores")
        sys.exit(1)
