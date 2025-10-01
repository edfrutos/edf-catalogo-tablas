#!/usr/bin/env python3
# Script para actualizar la lista blanca de IPs en MongoDB Atlas
# Creado: 18/05/2025

import datetime
import json
import os
import re
import socket
import subprocess
import sys

import requests
from dotenv import load_dotenv

# Configuración
LOG_FILE = "/logs/mongodb_whitelist.log"
CONFIG_FILE = "/config/mongodb_config.json"


def log(message):
    """Registra un mensaje en el archivo de log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def get_server_ip():
    """Obtiene la dirección IP pública del servidor"""
    try:
        # Método 1: Usando un servicio externo
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        if response.status_code == 200:
            ip = response.json().get("ip")
            log(f"IP obtenida de ipify.org: {ip}")
            return ip
    except Exception as e:
        log(f"Error al obtener IP de ipify.org: {e}")

    try:
        # Método 2: Usando otro servicio externo
        response = requests.get("https://ifconfig.me/ip", timeout=5)
        if response.status_code == 200:
            ip = response.text.strip()
            log(f"IP obtenida de ifconfig.me: {ip}")
            return ip
    except Exception as e:
        log(f"Error al obtener IP de ifconfig.me: {e}")

    try:
        # Método 3: Usando comandos del sistema
        result = subprocess.run(
            ["curl", "-s", "https://ifconfig.me"], capture_output=True, text=True
        )
        if result.returncode == 0:
            ip = result.stdout.strip()
            log(f"IP obtenida mediante curl: {ip}")
            return ip
    except Exception as e:
        log(f"Error al obtener IP mediante curl: {e}")

    log("No se pudo obtener la IP pública del servidor")
    return None


def extract_mongodb_info():
    """Extrae información de MongoDB de la URI en el archivo .env"""
    env_path = "/.env"
    if not os.path.exists(env_path):
        log(f"No se encontró el archivo {env_path}")
        return None

    with open(env_path) as f:
        content = f.read()

    # Buscar la URI de MongoDB
    mongo_uri_match = re.search(r"^MONGO_URI\s*=\s*(.*)$", content, re.MULTILINE)
    if not mongo_uri_match:
        log("No se encontró la URI de MongoDB en el archivo .env")
        return None

    mongo_uri = mongo_uri_match.group(1).strip()

    # Extraer información de la URI
    if mongo_uri.startswith("mongodb+srv://"):
        # URI SRV
        match = re.match(
            r"mongodb\+srv://([^:]+):([^@]+)@([^/]+)/([^?]+)(\?.*)?", mongo_uri
        )
        if not match:
            log("No se pudo analizar la URI de MongoDB")
            return None

        username, password, hostname, database, _ = match.groups()

        # Extraer el nombre del proyecto/grupo
        project_name = hostname.split(".")[0]

        return {
            "username": username,
            "password": password,
            "hostname": hostname,
            "database": database,
            "project_name": project_name,
        }
    elif mongo_uri.startswith("mongodb://"):
        # URI directa
        match = re.match(r"mongodb://([^:]+):([^@]+)@([^/]+)/([^?]+)(\?.*)?", mongo_uri)
        if not match:
            log("No se pudo analizar la URI de MongoDB")
            return None

        username, password, hosts, database, _ = match.groups()

        # Extraer el primer hostname
        hostname = hosts.split(",")[0].split(":")[0]

        # Intentar determinar el nombre del proyecto/grupo
        if "cluster" in hostname:
            parts = hostname.split(".")
            if len(parts) >= 2:
                project_name = parts[0].split("-")[0]
            else:
                project_name = "unknown"
        else:
            project_name = "unknown"

        return {
            "username": username,
            "password": password,
            "hostname": hostname,
            "database": database,
            "project_name": project_name,
        }
    else:
        log(f"Formato de URI no reconocido: {mongo_uri[:10]}...")
        return None


def save_config(config):
    """Guarda la configuración en un archivo JSON"""
    # Asegurarse de que el directorio existe
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    log(f"Configuración guardada en {CONFIG_FILE}")


def load_config():
    """Carga la configuración desde un archivo JSON"""
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE) as f:
        return json.load(f)


def generate_instructions():
    """Genera instrucciones para actualizar manualmente la lista blanca de IPs"""
    server_ip = get_server_ip()
    if not server_ip:
        return "No se pudo obtener la IP del servidor"

    mongodb_info = extract_mongodb_info()
    if not mongodb_info:
        return "No se pudo extraer la información de MongoDB"

    instructions = f"""
==========================================================
INSTRUCCIONES PARA ACTUALIZAR LA LISTA BLANCA DE IPS EN MONGODB ATLAS
==========================================================

1. Accede a MongoDB Atlas en https://cloud.mongodb.com
2. Inicia sesión con las credenciales:
   - Usuario: {mongodb_info['username']}
   - Contraseña: (la contraseña almacenada en el archivo .env)
3. Selecciona tu proyecto: {mongodb_info['project_name']}
4. En el menú de la izquierda, haz clic en "Network Access"
5. Haz clic en el botón "ADD IP ADDRESS"
6. Añade la siguiente dirección IP: {server_ip}
7. En la descripción, escribe: "Servidor de producción edefrutos2025"
8. Haz clic en "Confirm"

La IP del servidor ({server_ip}) ahora debería estar en la lista blanca y permitir conexiones a MongoDB Atlas.

==========================================================
"""

    # Guardar la configuración
    config = {
        "server_ip": server_ip,
        "mongodb_info": mongodb_info,
        "last_updated": datetime.datetime.now().isoformat(),
    }
    save_config(config)

    return instructions


def main():
    """Función principal"""
    # Asegurarse de que el directorio de logs existe
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log(
        "Generando instrucciones para actualizar la lista blanca de IPs en MongoDB Atlas..."
    )

    instructions = generate_instructions()

    log("Instrucciones generadas correctamente")
    print("\n" + instructions)

    # Guardar las instrucciones en un archivo
    instructions_file = "/docs/mongodb_whitelist_instructions.txt"
    os.makedirs(os.path.dirname(instructions_file), exist_ok=True)

    with open(instructions_file, "w") as f:
        f.write(instructions)

    log(f"Instrucciones guardadas en {instructions_file}")

    print(f"\nLas instrucciones también se han guardado en {instructions_file}")


if __name__ == "__main__":
    main()
