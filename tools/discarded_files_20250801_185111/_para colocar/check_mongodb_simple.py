#!/usr/bin/env python3
# Script simplificado para verificar la conexión a MongoDB
# Creado: 18/05/2025
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import argparse
import datetime
import json
import os
import pathlib
import re
import socket
import subprocess
import sys

from dotenv import load_dotenv

parser = argparse.ArgumentParser(
    description="Verificación simple de conexión a MongoDB. No requiere argumentos."
)
args = parser.parse_args()

# Detectar si estamos en local (hay .env en el cwd o superior) o en servidor
cwd = pathlib.Path(os.getcwd())
local_env = None
for parent in [cwd] + list(cwd.parents):
    env_path = parent / ".env"
    if env_path.exists():
        local_env = str(env_path)
        break

if local_env:
    ROOT_DIR = str(pathlib.Path(local_env).parent)
    ENV_FILE = local_env
    print(f"[INFO] Ejecutando en entorno LOCAL. Usando .env en: {ENV_FILE}")
else:
    ROOT_DIR = "/"
    ENV_FILE = os.path.join(ROOT_DIR, ".env")
    print(f"[INFO] Ejecutando en entorno SERVIDOR. Usando .env en: {ENV_FILE}")


def print_header(message):
    print("\n" + "=" * 80)
    print(f"{message}".center(80))
    print("=" * 80)


def check_mongo_uri():
    """Verifica la URI de MongoDB en el archivo .env"""
    print(f"Verificando URI de MongoDB en {ENV_FILE}")

    # Cargar variables de entorno
    load_dotenv(ENV_FILE)

    # Obtener la URI de MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("  ❌ No se encontró la variable MONGO_URI en el archivo .env")
        return None

    # Ocultar la contraseña para mostrarla
    safe_uri = re.sub(r"(:)([^@]+)(@)", r"\1****\3", mongo_uri)
    print(f"  ✅ URI de MongoDB encontrada: {safe_uri}")

    return mongo_uri


def extract_mongo_host_port(mongo_uri):
    """Extrae el host y puerto de la URI de MongoDB"""
    try:
        # Extraer host y puerto usando expresiones regulares
        match = re.search(
            r"mongodb(?:\+srv)?://(?:[^:@]+:[^@]+@)?([^/:]+)(?::(\d+))?", mongo_uri
        )
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 27017
            return host, port
        return None, None
    except Exception as e:
        print(f"  ❌ Error al extraer host y puerto: {e}")
        return None, None


def check_network_connectivity(host, port):
    """Verifica la conectividad de red a un host y puerto específicos"""
    print(f"Verificando conectividad de red a {host}:{port}")

    try:
        # Resolver el hostname a IP
        try:
            ip_address = socket.gethostbyname(host)
            print(f"  ✅ Resolución DNS exitosa: {host} -> {ip_address}")
        except socket.gaierror as e:
            print(f"  ❌ Error de resolución DNS: {e}")
            return False

        # Crear un socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # Intentar conectar
        result = sock.connect_ex((ip_address, port))

        if result == 0:
            print(f"  ✅ Conexión exitosa a {host}:{port}")
            sock.close()
            return True
        else:
            print(
                f"  ❌ No se pudo conectar a {host}:{port} (código de error: {result})"
            )
            sock.close()
            return False
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        return False


def check_mongodb_status():
    """Verifica el estado de MongoDB usando comandos del sistema"""
    print("Verificando estado de MongoDB en la aplicación...")

    try:
        # Verificar si hay procesos de MongoDB en ejecución
        ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "mongod" in ps_result.stdout:
            print("  ✅ Proceso de MongoDB encontrado en ejecución")
        else:
            print(
                "  ℹ️ No se encontraron procesos de MongoDB en ejecución (normal si se usa MongoDB Atlas)"
            )

        # Verificar logs recientes de la aplicación
        log_path = os.path.join(ROOT_DIR, "logs", "app.log")
        if not os.path.exists(log_path):
            # Buscar logs en local si no existe en ROOT_DIR
            alt_log = os.path.join(os.getcwd(), "logs", "app.log")
            if os.path.exists(alt_log):
                log_path = alt_log
        if os.path.exists(log_path):
            tail_result = subprocess.run(
                ["tail", "-n", "50", log_path], capture_output=True, text=True
            )

            if "MongoDB connection error" in tail_result.stdout:
                print(
                    "  ❌ Se encontraron errores de conexión a MongoDB en los logs recientes"
                )
                return False
            elif "Connected to MongoDB" in tail_result.stdout:
                print(
                    "  ✅ La aplicación se conectó correctamente a MongoDB según los logs recientes"
                )
                return True

        # Si no podemos determinar el estado por los logs, asumimos que está bien
        return True
    except Exception as e:
        print(f"  ❌ Error al verificar el estado de MongoDB: {e}")
        return False


def main():
    print_header("VERIFICACIÓN SIMPLE DE CONEXIÓN A MONGODB")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Verificar URI de MongoDB
    mongo_uri = check_mongo_uri()
    if not mongo_uri:
        print_header("RESULTADO")
        print("❌ No se pudo verificar la conexión a MongoDB: URI no encontrada")
        return False

    # Extraer host y puerto
    host, port = extract_mongo_host_port(mongo_uri)
    if not host:
        print_header("RESULTADO")
        print("❌ No se pudo extraer el host y puerto de la URI de MongoDB")
        return False

    # Verificar conectividad de red
    network_ok = check_network_connectivity(host, port)

    # Verificar estado de MongoDB en la aplicación
    app_mongo_ok = check_mongodb_status()

    print_header("RESULTADO")
    if network_ok and app_mongo_ok:
        print("✅ La conexión a MongoDB parece estar funcionando correctamente")
        return True
    elif network_ok:
        print(
            "⚠️ Hay conectividad de red a MongoDB, pero la aplicación puede tener problemas de conexión"
        )
        return True
    else:
        print("❌ No hay conectividad de red a MongoDB")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
