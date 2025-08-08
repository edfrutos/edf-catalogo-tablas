#!/usr/bin/env python3
"""
Utilidades de monitoreo para scripts de mantenimiento.
Incluye alertas, métricas y notificaciones.
"""

import os
import sys
import json
import logging
import smtplib
import psutil
import platform
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional


# Importar configuración
def get_config():
    """Obtiene la configuración de mantenimiento."""
    try:
        # Intentar importar desde el mismo directorio
        import sys
        from pathlib import Path

        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))

        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "config", current_dir / "config.py"
        )
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module.config
    except ImportError:
        # Si aún no se puede importar, crear una configuración mínima
        class MinimalConfig:
            MAINTENANCE_LOGS_DIR = Path(__file__).parent / "logs"
            LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
            LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
            SEND_EMAIL = False
            EMAIL_FROM = ""
            EMAIL_TO = ""
            EMAIL_SERVER = ""
            EMAIL_PORT = 587
            EMAIL_USER = ""
            EMAIL_PASSWORD = ""
            DISK_USAGE_THRESHOLD = 80
            MEMORY_USAGE_THRESHOLD = 85

        return MinimalConfig()


# Obtener la configuración
config = get_config()


class SystemMonitor:
    """Monitor del sistema con alertas y métricas."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.alerts: List[str] = []
        self.metrics: Dict[str, Any] = {}

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Recopila métricas del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=True)

            # Memoria
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disco
            disk = psutil.disk_usage("/")

            # Red
            network = psutil.net_io_counters()

            # Sistema
            system_info = {
                "platform": platform.system(),
                "release": platform.release(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
            }

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": system_info,
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": cpu_count,
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2),
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": disk.percent,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
            }

            self.metrics = metrics
            return metrics

        except Exception as e:
            self.logger.error(f"Error recopilando métricas del sistema: {e}")
            return {}

    def check_alerts(self) -> List[str]:
        """Verifica si hay alertas basadas en las métricas."""
        alerts: List[str] = []

        if not self.metrics:
            return alerts

        # Alerta de uso de CPU
        cpu_usage = self.metrics.get("cpu", {}).get("usage_percent", 0)
        if cpu_usage > 90:
            alerts.append(f"🚨 CPU usage crítico: {cpu_usage}%")
        elif cpu_usage > 80:
            alerts.append(f"⚠️ CPU usage alto: {cpu_usage}%")

        # Alerta de uso de memoria
        memory_usage = self.metrics.get("memory", {}).get("usage_percent", 0)
        if memory_usage > config.MEMORY_USAGE_THRESHOLD:
            alerts.append(f"🚨 Memoria usage crítico: {memory_usage}%")
        elif memory_usage > 75:
            alerts.append(f"⚠️ Memoria usage alto: {memory_usage}%")

        # Alerta de uso de disco
        disk_usage = self.metrics.get("disk", {}).get("usage_percent", 0)
        if disk_usage > config.DISK_USAGE_THRESHOLD:
            alerts.append(f"🚨 Disco usage crítico: {disk_usage}%")
        elif disk_usage > 70:
            alerts.append(f"⚠️ Disco usage alto: {disk_usage}%")

        self.alerts = alerts
        return alerts

    def save_metrics(self, filename: Optional[str] = None) -> str:
        """Guarda las métricas en un archivo JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_metrics_{timestamp}.json"

        metrics_file = config.MAINTENANCE_LOGS_DIR / filename

        try:
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Métricas guardadas en: {metrics_file}")
            return str(metrics_file)

        except Exception as e:
            self.logger.error(f"Error guardando métricas: {e}")
            return ""

    def send_alert_email(self, subject: str, body: str) -> bool:
        """Envía un correo de alerta."""
        if not config.SEND_EMAIL:
            self.logger.info("Envío de correo desactivado")
            return False

        if not all(
            [
                config.EMAIL_FROM,
                config.EMAIL_TO,
                config.EMAIL_SERVER,
                config.EMAIL_USER,
                config.EMAIL_PASSWORD,
            ]
        ):
            self.logger.warning("Faltan datos para enviar correo")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = config.EMAIL_FROM
            msg["To"] = config.EMAIL_TO
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(config.EMAIL_SERVER, config.EMAIL_PORT)
            server.starttls()
            server.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Alerta enviada a {config.EMAIL_TO}")
            return True

        except Exception as e:
            self.logger.error(f"Error enviando alerta: {e}")
            return False

    def generate_alert_report(self) -> str:
        """Genera un reporte HTML de alertas."""
        if not self.alerts:
            return "<p>✅ No hay alertas activas</p>"

        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .alert { padding: 10px; margin: 5px 0; border-radius: 5px; }
                .critical { background-color: #ffebee; border-left: 4px solid #f44336; }
                .warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
                .metrics { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h2>🚨 Alertas del Sistema</h2>
        """

        for alert in self.alerts:
            css_class = "critical" if "🚨" in alert else "warning"
            html += f'<div class="alert {css_class}">{alert}</div>'

        if self.metrics:
            html += "<h3>📊 Métricas del Sistema</h3>"
            html += '<div class="metrics">'
            html += f"<p><strong>CPU:</strong> {self.metrics.get('cpu', {}).get('usage_percent', 0)}%</p>"
            html += f"<p><strong>Memoria:</strong> {self.metrics.get('memory', {}).get('usage_percent', 0)}%</p>"
            html += f"<p><strong>Disco:</strong> {self.metrics.get('disk', {}).get('usage_percent', 0)}%</p>"
            html += "</div>"

        html += f"<p><small>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>"
        html += "</body></html>"

        return html


class LogAnalyzer:
    """Analizador de logs para detectar patrones y problemas."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze_log_file(self, log_file: Path, hours: int = 24) -> Dict[str, Any]:
        """Analiza un archivo de log para detectar patrones."""
        if not log_file.exists():
            return {"error": "Archivo de log no encontrado"}

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            error_count = 0
            warning_count = 0
            info_count = 0
            recent_errors = []

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # Parsear timestamp del log
                        timestamp_str = line[:19]  # "2025-08-08 16:22:44"
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if log_time >= cutoff_time:
                            if "ERROR" in line:
                                error_count += 1
                                recent_errors.append(line.strip())
                            elif "WARNING" in line:
                                warning_count += 1
                            elif "INFO" in line:
                                info_count += 1
                    except ValueError:
                        continue

            return {
                "period_hours": hours,
                "total_lines": error_count + warning_count + info_count,
                "errors": error_count,
                "warnings": warning_count,
                "info": info_count,
                "recent_errors": recent_errors[-10:],  # Últimos 10 errores
            }

        except Exception as e:
            self.logger.error(f"Error analizando log {log_file}: {e}")
            return {"error": str(e)}


# Funciones de utilidad
def setup_monitoring_logger(name: str = "monitoring") -> logging.Logger:
    """Configura un logger específico para monitoreo."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evitar duplicar handlers
    if not logger.handlers:
        formatter = logging.Formatter(config.LOG_FORMAT, config.LOG_DATE_FORMAT)

        # Handler para archivo
        log_file = config.MAINTENANCE_LOGS_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
