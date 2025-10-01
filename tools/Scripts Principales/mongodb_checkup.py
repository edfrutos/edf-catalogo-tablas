#!/usr/bin/env python3
# Script global para chequeo y monitorización de MongoDB
# Ejecutable en local y servidor, con modo diagnóstico y monitor

from app import notifications
import argparse
import os
import socket
import sys
import time
from datetime import datetime

import certifi
import dns.resolver
import pymongo
from dotenv import load_dotenv
from pymongo.errors import (
    ConfigurationError,
    OperationFailure,
    ServerSelectionTimeoutError,
)

# Importar sistema de notificaciones de la app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


def print_header(message):
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)


def check_dns_resolution(hostname):
    print(f"Verificando resolución DNS para: {hostname}")
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"  Resolución exitosa: {hostname} -> {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"  Error de resolución DNS: {e}")
        return False


def check_srv_records(hostname):
    print(f"Verificando registros SRV para: _mongodb._tcp.{hostname}")
    try:
        answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", "SRV")
        print(f"  Registros SRV encontrados: {len(answers)}")
        for rdata in list(answers):
            print(
                f"  {rdata.target} (prioridad: {rdata.priority}, peso: {rdata.weight}, puerto: {rdata.port})"
            )
        return True
    except Exception as e:
        print(f"  Error al resolver registros SRV: {e}")
        return False


def check_network_connectivity(host, port):
    print(f"Verificando conectividad de red a {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"  Conexión exitosa a {host}:{port}")
            sock.close()
            return True
        else:
            print(f"  No se pudo conectar a {host}:{port} (código de error: {result})")
            sock.close()
            return False
    except socket.gaierror as e:
        print(f"  Error de resolución de dirección: {e}")
        return False
    except OSError as e:
        print(f"  Error de socket: {e}")
        return False


def test_mongodb_connection(uri):
    print(
        f"Probando conexión a MongoDB con URI: {uri[:30]}... (ocultando credenciales)"
    )
    try:
        client = pymongo.MongoClient(
            uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where()
        )
        server_info = client.server_info()
        print("  Conexión exitosa a MongoDB")
        print(f"  Versión del servidor: {server_info.get('version', 'desconocida')}")
        databases = client.list_database_names()
        print(f"  Bases de datos disponibles: {', '.join(databases)}")
        return True, None
    except ConfigurationError as e:
        return False, f"Error de configuración: {str(e)}"
    except ServerSelectionTimeoutError as e:
        return False, f"Timeout al conectar al servidor: {str(e)}"
    except OperationFailure as e:
        return (
            False,
            f"Error de operación (posiblemente credenciales incorrectas): {str(e)}",
        )
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


def check_logs(logs_dir="logs", max_lines=200):
    print(f"Chequeando logs en {logs_dir} (últimas {max_lines} líneas por archivo)")
    issues = []
    if not os.path.exists(logs_dir):
        print(f"  No existe el directorio de logs: {logs_dir}")
        return issues
    for fname in os.listdir(logs_dir):
        if fname.endswith(".log"):
            fpath = os.path.join(logs_dir, fname)
            try:
                with open(fpath) as f:
                    lines = f.readlines()[-max_lines:]
                    for line in lines:
                        if any(x in line for x in ["ERROR", "Exception", "Traceback"]):
                            issues.append(f"{fname}: {line.strip()}")
            except Exception as e:
                print(f"  Error leyendo {fname}: {e}")
    if issues:
        print(f"  Se encontraron {len(issues)} posibles incidencias en los logs.")
    else:
        print("  No se encontraron incidencias en los logs.")
    return issues


def enviar_resumen_alerta(subject, error, issues):
    """Envía un resumen HTML de los errores/incidencias usando el sistema de notificaciones"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html><body>
    <h2>Alerta de chequeo MongoDB - {subject}</h2>
    <p><b>Fecha y hora:</b> {now}</p>
    <p><b>Error de conexión:</b> {error or 'Sin error de conexión'}</p>
    <h3>Incidencias en logs:</h3>
    <ul>
    {''.join(f'<li>{line}</li>' for line in issues) if issues else '<li>No se detectaron incidencias en los logs.</li>'}
    </ul>
    <hr>
    <p>Este mensaje ha sido generado automáticamente por el sistema de chequeo global.</p>
    </body></html>
    """
    notifications.send_email(subject, html)


def main():
    print_header("CHEQUEO GLOBAL DE MONGODB Y SISTEMA")
    load_dotenv()
    env = dict(os.environ)
    parser = argparse.ArgumentParser(description="Chequeo y monitorización de MongoDB")
    parser.add_argument(
        "--mode",
        choices=["diagnostic", "monitor"],
        help="Modo de ejecución: diagnóstico rápido o monitor completo",
    )
    parser.add_argument(
        "--logs-dir",
        default="logs",
        help="Directorio de logs a analizar (solo modo monitor)",
    )
    parser.add_argument(
        "--email-alerts",
        action="store_true",
        help="Enviar alertas por email si hay problemas (solo modo monitor)",
    )
    args = parser.parse_args()

    # Preguntar modo si no se pasa por argumento
    mode = args.mode
    if not mode:
        mode = (
            input("¿Modo de ejecución? [diagnostic/monitor]: ").strip().lower()
            or "diagnostic"
        )
    print(f"\nModo seleccionado: {mode}")

    # Leer URI de MongoDB
    mongo_uri = env.get("MONGO_URI")
    while not mongo_uri:
        mongo_uri = input("Introduce la URI de MongoDB (MONGO_URI): ").strip()
    # Extraer hostname
    try:
        hostname = mongo_uri.split("@")[1].split("/")[0]
    except Exception:
        hostname = ""
    # Chequeos básicos
    print_header("VERIFICACIÓN DE DNS Y SRV")
    dns_ok = check_dns_resolution(hostname)
    srv_ok = check_srv_records(hostname)
    print_header("VERIFICACIÓN DE CONECTIVIDAD DE RED")
    check_network_connectivity("8.8.8.8", 53)
    check_network_connectivity(hostname, 27017)
    print_header("PRUEBA DE CONEXIÓN A MONGODB")
    success, error = test_mongodb_connection(mongo_uri)
    print_header("RESUMEN DE RESULTADOS")
    if success:
        print("✅ La conexión a MongoDB fue exitosa")
    else:
        print(f"❌ Error al conectar a MongoDB: {error}")
    # Si modo monitor, analizar logs y alertar
    if mode == "monitor":
        print_header("ANÁLISIS DE LOGS")
        issues = check_logs(args.logs_dir)
        if not success or issues:
            print(
                "\n❗ Se detectaron problemas. Puedes revisar los logs o recibir alerta por email."
            )
            if args.email_alerts:
                subject = "[ALERTA] Problemas detectados en MongoDB o logs"
                enviar_resumen_alerta(subject, error, issues)
        else:
            print("\n✅ No se detectaron problemas graves en modo monitor.")
    print(
        "\nChequeo finalizado. Fecha y hora:",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


if __name__ == "__main__":
    main()
