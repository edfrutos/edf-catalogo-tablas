#!/usr/bin/env python3
# Script para verificar la conexión a MongoDB compatible con diferentes versiones de PyOpenSSL
# Creado: 18/05/2025

import os
import sys
import socket
import datetime
import subprocess
import json
from dotenv import load_dotenv

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(ROOT_DIR, '.env')

# Si no existe el archivo .env en la ruta principal, buscar en otras ubicaciones comunes
if not os.path.exists(ENV_FILE):
    possible_env_files = [
        os.path.join(ROOT_DIR, 'httpdocs', '.env'),
        '/.env',
        os.path.join(os.path.expanduser('~'), '.env')
    ]
    
    for env_file in possible_env_files:
        if os.path.exists(env_file):
            ENV_FILE = env_file
            break

def print_header(message):
    print("\n" + "="*80)
    print(f"{message}".center(80))
    print("="*80)

def check_dns_resolution(hostname):
    """Verifica la resolución DNS de un hostname"""
    print(f"Verificando resolución DNS para: {hostname}")
    try:
        # Intentar resolver el hostname
        ip_address = socket.gethostbyname(hostname)
        print(f"  Resolución exitosa: {hostname} -> {ip_address}")
        return True, ip_address
    except socket.gaierror as e:
        print(f"  Error de resolución DNS: {e}")
        return False, None

def check_network_connectivity(host, port):
    """Verifica la conectividad de red a un host y puerto específicos"""
    print(f"Verificando conectividad de red a {host}:{port}")
    
    try:
        # Crear un socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Intentar conectar
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
    except socket.error as e:
        print(f"  Error de socket: {e}")
        return False

def check_mongo_uri():
    """Verifica la URI de MongoDB en el archivo .env"""
    print(f"Verificando URI de MongoDB en {ENV_FILE}")
    
    # Cargar variables de entorno
    load_dotenv(ENV_FILE)
    
    # Obtener la URI de MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("  ❌ No se encontró la variable MONGO_URI en el archivo .env")
        return None
    
    print(f"  ✅ URI de MongoDB encontrada: {mongo_uri[:20]}...")
    return mongo_uri

def check_mongodb_connection():
    """Verifica la conexión a MongoDB usando un script externo"""
    print("Verificando conexión a MongoDB...")
    
    # Crear un script temporal para probar la conexión
    temp_script = """
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URI de MongoDB
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    print("No se encontró la variable MONGO_URI en el archivo .env")
    sys.exit(1)

# Intentar conectar a MongoDB
try:
    # Intentar importar pymongo
    try:
        import pymongo
        import certifi
    except ImportError:
        print("No se pudo importar pymongo o certifi")
        sys.exit(1)
    
    # Crear cliente de MongoDB
    try:
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        client.admin.command('ping')
        print("Conexión exitosa a MongoDB")
        
        # Listar bases de datos
        databases = client.list_database_names()
        print(f"Bases de datos disponibles: {', '.join(databases)}")
        
        # Listar colecciones de la base de datos actual
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"Colecciones en {db_name}: {', '.join(collections)}")
        
        sys.exit(0)
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        sys.exit(1)
except Exception as e:
    print(f"Error general: {e}")
    sys.exit(1)
"""
    
    # Guardar el script temporal
    tools_dir = os.path.join(ROOT_DIR, 'tools')
    if not os.path.exists(tools_dir):
        tools_dir = '/tools'
    temp_script_path = os.path.join(tools_dir, 'temp_check_mongodb.py')
    with open(temp_script_path, 'w') as f:
        f.write(temp_script)
    
    try:
        # Ejecutar el script temporal
        venv_python = os.path.join(ROOT_DIR, '.venv', 'bin', 'python')
        if os.path.exists(venv_python):
            result = subprocess.run([venv_python, temp_script_path], capture_output=True, text=True)
        else:
            result = subprocess.run(['python3', temp_script_path], capture_output=True, text=True)
        
        # Mostrar la salida
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Eliminar el script temporal
        os.remove(temp_script_path)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error al ejecutar el script: {e}")
        
        # Eliminar el script temporal
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        
        return False

def main():
    print_header("VERIFICACIÓN DE CONEXIÓN A MONGODB")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar URI de MongoDB
    mongo_uri = check_mongo_uri()
    if not mongo_uri:
        print_header("RESULTADO")
        print("❌ No se pudo verificar la conexión a MongoDB: URI no encontrada")
        return False
    
    # Verificar conexión a MongoDB
    connection_success = check_mongodb_connection()
    
    print_header("RESULTADO")
    if connection_success:
        print("✅ Conexión a MongoDB exitosa")
        return True
    else:
        print("❌ No se pudo conectar a MongoDB")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
