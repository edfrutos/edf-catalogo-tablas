#!/usr/bin/env python3
# Script para monitorear la conexión a MongoDB y el estado de la aplicación
# Creado: 18/05/2025

import datetime
import json
import os
import re
import smtplib
import socket
import subprocess
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Configuración
BASE_DIR = "/Users/edefrutos/edf_catalogotablas"
LOG_FILE = f"{BASE_DIR}/logs/mongodb_monitor.log"
GUNICORN_ERROR_LOG = f"{BASE_DIR}/logs/gunicorn_error.log"
GUNICORN_ACCESS_LOG = f"{BASE_DIR}/logs/gunicorn_access.log"
APP_LOG = f"{BASE_DIR}/logs/app.log"
CRON_MONITOR_LOG = f"{BASE_DIR}/logs/cron_monitor.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB

# Inicializar archivo de log si no existe
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        f.write(f"# Log de monitoreo de MongoDB - Iniciado: {datetime.datetime.now()}\n")

def log(message):
    """Registra un mensaje en el archivo de log"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def rotate_log_if_needed(log_file):
    """Rota el archivo de log si excede el tamaño máximo"""
    if os.path.exists(log_file) and os.path.getsize(log_file) > MAX_LOG_SIZE:
        backup_file = f"{log_file}.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(log_file, backup_file)
        log(f"Archivo de log rotado: {log_file} -> {backup_file}")
        with open(log_file, 'w') as f:
            f.write(f"# Log rotado: {datetime.datetime.now()}\n")

def check_mongodb_connection():
    """Verifica la conexión a MongoDB"""
    log("Verificando conexión a MongoDB...")

    # Intentar extraer la URI de MongoDB del archivo .env
    env_path = f"{BASE_DIR}/.env"
    mongo_uri = None

    if os.path.exists(env_path):
        with open(env_path) as f:
            content = f.read()
            mongo_uri_match = re.search(r'^MONGO_URI\s*=\s*(.*)$', content, re.MULTILINE)
            if mongo_uri_match:
                mongo_uri = mongo_uri_match.group(1).strip()

    if not mongo_uri:
        log("No se pudo extraer la URI de MongoDB del archivo .env")
        return False, "URI no encontrada"

    # Determinar si es una URI directa o SRV
    is_srv = mongo_uri.startswith("mongodb+srv://")

    # Extraer el hostname
    hostname_match = None
    if is_srv:
        hostname_match = re.search(r'mongodb\+srv://[^@]+@([^/]+)', mongo_uri)
    else:
        hostname_match = re.search(r'mongodb://[^@]+@([^/:]+)', mongo_uri)

    if not hostname_match:
        log("No se pudo extraer el hostname de la URI de MongoDB")
        return False, "Hostname no encontrado"

    hostname = hostname_match.group(1)

    # Verificar resolución DNS
    try:
        ip_address = socket.gethostbyname(hostname)
        log(f"Resolución DNS exitosa: {hostname} -> {ip_address}")
    except socket.gaierror as e:
        log(f"Error de resolución DNS: {e}")
        return False, f"Error DNS: {e}"

    # Verificar conectividad de red
    try:
        # Crear un script temporal para probar la conexión
        test_script = """
import sys
import pymongo
import certifi
import time

uri = sys.argv[1]
try:
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
    client.admin.command('ping')
    print("Conexión exitosa a MongoDB")
    sys.exit(0)
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")
    sys.exit(1)
"""
        test_script_path = "/tmp/test_mongodb_connection.py"
        with open(test_script_path, 'w') as f:
            f.write(test_script)

        # Ejecutar el script
        result = subprocess.run([
            f"{BASE_DIR}/venv310/bin/python",
            test_script_path,
            mongo_uri
        ], capture_output=True, text=True)

        # Eliminar el script temporal
        os.remove(test_script_path)

        if result.returncode == 0:
            log("Conexión a MongoDB exitosa")
            return True, "Conexión exitosa"
        else:
            log(f"Error al conectar a MongoDB: {result.stderr.strip()}")
            return False, result.stderr.strip()

    except Exception as e:
        log(f"Error al verificar la conexión a MongoDB: {e}")
        return False, str(e)

def check_application_status():
    """Verifica el estado de la aplicación"""
    log("Verificando estado de la aplicación...")

    # Verificar si el servicio Gunicorn está en ejecución
    try:
        result = subprocess.run(["systemctl", "is-active", "edefrutos2025"], capture_output=True, text=True)
        service_status = result.stdout.strip()

        if service_status == "active":
            log("Servicio Gunicorn activo")
        else:
            log(f"Servicio Gunicorn no activo: {service_status}")
            return False, f"Servicio inactivo: {service_status}"

        # Verificar si el proceso está escuchando en el puerto correcto
        result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
        if "127.0.0.1:8002" in result.stdout:
            log("Proceso escuchando en el puerto 8002")
        else:
            log("Proceso no escuchando en el puerto 8002")
            return False, "Puerto 8002 no disponible"

        # Verificar si hay errores recientes en los logs
        recent_errors = []

        if os.path.exists(GUNICORN_ERROR_LOG):
            with open(GUNICORN_ERROR_LOG) as f:
                # Leer las últimas 100 líneas
                lines = f.readlines()[-100:]
                for line in lines:
                    if "ERROR" in line or "Exception" in line:
                        recent_errors.append(line.strip())

        if recent_errors:
            log(f"Se encontraron {len(recent_errors)} errores recientes en los logs")
            return False, f"{len(recent_errors)} errores recientes"

        # Verificar si la aplicación responde
        try:
            result = subprocess.run(["curl", "-s", "-I", "http://127.0.0.1:8002"], capture_output=True, text=True)
            if result.returncode == 0 and "200 OK" in result.stdout:
                log("Aplicación responde correctamente")
            else:
                log("Aplicación no responde correctamente")
                return False, "Aplicación no responde"
        except Exception as e:
            log(f"Error al verificar la respuesta de la aplicación: {e}")
            return False, f"Error de respuesta: {e}"

        return True, "Aplicación funcionando correctamente"

    except Exception as e:
        log(f"Error al verificar el estado de la aplicación: {e}")
        return False, str(e)

def analyze_logs():
    """Analiza los logs para detectar problemas"""
    log("Analizando logs...")

    issues = []

    # Verificar logs de Gunicorn
    if os.path.exists(GUNICORN_ERROR_LOG):
        with open(GUNICORN_ERROR_LOG) as f:
            # Leer las últimas 200 líneas
            lines = f.readlines()[-200:]
            for line in lines:
                if "ERROR" in line or "Exception" in line:
                    issues.append(f"Error en Gunicorn: {line.strip()}")

    # Verificar logs de la aplicación
    if os.path.exists(APP_LOG):
        with open(APP_LOG) as f:
            # Leer las últimas 200 líneas
            lines = f.readlines()[-200:]
            for line in lines:
                if "ERROR" in line or "Exception" in line:
                    issues.append(f"Error en la aplicación: {line.strip()}")

    # Verificar logs de acceso para detectar errores HTTP
    if os.path.exists(GUNICORN_ACCESS_LOG):
        with open(GUNICORN_ACCESS_LOG) as f:
            # Leer las últimas 200 líneas
            lines = f.readlines()[-200:]
            for line in lines:
                if " 500 " in line or " 502 " in line or " 503 " in line or " 504 " in line:
                    issues.append(f"Error HTTP: {line.strip()}")

    if issues:
        log(f"Se encontraron {len(issues)} problemas en los logs")
        return issues
    else:
        log("No se encontraron problemas en los logs")
        return []

def send_alert_email(subject, message):
    """Envía un correo electrónico de alerta"""
    # Cargar variables de entorno
    load_dotenv(f"{BASE_DIR}/.env")

    # Configuración de correo
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    alert_email = os.getenv("ALERT_EMAIL", "admin@edefrutos2025.xyz")

    if not smtp_user or not smtp_password or not alert_email:
        log("No se pudo enviar alerta por correo: falta configuración de SMTP")
        return False

    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = alert_email
        msg["Subject"] = subject

        # Añadir cuerpo del mensaje
        msg.attach(MIMEText(message, "plain"))

        # Conectar al servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        # Enviar correo
        server.send_message(msg)
        server.quit()

        log(f"Alerta enviada por correo a {alert_email}")
        return True

    except Exception as e:
        log(f"Error al enviar alerta por correo: {e}")
        return False

def fix_mongodb_connection():
    """Intenta corregir problemas de conexión a MongoDB"""
    log("Intentando corregir problemas de conexión a MongoDB...")

    try:
        # Ejecutar el script de solución
        fix_script = f"{BASE_DIR}/tools/fix_mongodb_atlas.py"
        if os.path.exists(fix_script):
            result = subprocess.run([
                f"{BASE_DIR}/venv310/bin/python",
                fix_script
            ], capture_output=True, text=True)

            if result.returncode == 0:
                log("Problemas de conexión a MongoDB corregidos correctamente")
                return True, "Corrección exitosa"
            else:
                log(f"Error al corregir problemas de conexión a MongoDB: {result.stderr.strip()}")
                return False, result.stderr.strip()
        else:
            log(f"No se encontró el script de solución: {fix_script}")
            return False, "Script no encontrado"

    except Exception as e:
        log(f"Error al intentar corregir problemas de conexión a MongoDB: {e}")
        return False, str(e)

def restart_application():
    """Reinicia la aplicación"""
    log("Reiniciando la aplicación...")

    try:
        # Ejecutar el script de reinicio
        restart_script = f"{BASE_DIR}/tools/restart_server.sh"
        if os.path.exists(restart_script):
            result = subprocess.run([restart_script], capture_output=True, text=True)

            if result.returncode == 0:
                log("Aplicación reiniciada correctamente")
                return True, "Reinicio exitoso"
            else:
                log(f"Error al reiniciar la aplicación: {result.stderr.strip()}")
                return False, result.stderr.strip()
        else:
            # Intentar reiniciar con systemctl
            result = subprocess.run(["systemctl", "restart", "edefrutos2025"], capture_output=True, text=True)

            if result.returncode == 0:
                log("Aplicación reiniciada correctamente con systemctl")
                return True, "Reinicio exitoso"
            else:
                log(f"Error al reiniciar la aplicación con systemctl: {result.stderr.strip()}")
                return False, result.stderr.strip()

    except Exception as e:
        log(f"Error al reiniciar la aplicación: {e}")
        return False, str(e)

def main():
    """Función principal"""
    log("Iniciando monitoreo de MongoDB y aplicación...")

    # Rotar logs si es necesario
    rotate_log_if_needed(LOG_FILE)
    rotate_log_if_needed(GUNICORN_ERROR_LOG)
    rotate_log_if_needed(GUNICORN_ACCESS_LOG)
    rotate_log_if_needed(APP_LOG)

    # Verificar conexión a MongoDB
    mongodb_status, mongodb_message = check_mongodb_connection()

    # Verificar estado de la aplicación
    app_status, app_message = check_application_status()

    # Analizar logs
    log_issues = analyze_logs()

    # Determinar si hay problemas
    has_problems = not mongodb_status or not app_status or log_issues

    # Generar informe
    report = f"""
==========================================================
INFORME DE MONITOREO - {datetime.datetime.now()}
==========================================================

Estado de MongoDB: {"✅ OK" if mongodb_status else "❌ ERROR"}
Detalles: {mongodb_message}

Estado de la aplicación: {"✅ OK" if app_status else "❌ ERROR"}
Detalles: {app_message}

Problemas en logs: {"❌ " + str(len(log_issues)) + " problemas encontrados" if log_issues else "✅ Ninguno"}
"""

    if log_issues:
        report += "\nDetalles de problemas en logs:\n"
        for i, issue in enumerate(log_issues[:10], 1):
            report += f"{i}. {issue}\n"

        if len(log_issues) > 10:
            report += f"... y {len(log_issues) - 10} problemas más\n"

    report += "\n==========================================================\n"

    # Registrar informe
    log(report)

    # Si hay problemas, intentar solucionarlos
    if has_problems:
        log("Se detectaron problemas. Intentando solucionar...")

        # Si hay problemas con MongoDB, intentar corregirlos
        if not mongodb_status:
            fix_status, fix_message = fix_mongodb_connection()
            log(f"Resultado de la corrección de MongoDB: {fix_message}")

        # Si hay problemas con la aplicación, intentar reiniciarla
        if not app_status or not mongodb_status:
            restart_status, restart_message = restart_application()
            log(f"Resultado del reinicio de la aplicación: {restart_message}")

        # Enviar alerta por correo
        send_alert_email(
            "⚠️ Alerta: Problemas detectados en la aplicación",
            report + "\n\nSe han tomado medidas automáticas para solucionar los problemas."
        )
    else:
        log("No se detectaron problemas. Todo funciona correctamente.")

    log("Monitoreo finalizado.")

if __name__ == "__main__":
    main()
