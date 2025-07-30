#!/usr/bin/env python3
# Script para verificar la conexión a MongoDB
# Creado: 17/05/2025

import os
import sys
import pymongo
import certifi
import socket
import dns.resolver
import time
from dotenv import load_dotenv

def print_header(message):
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80)

def check_dns_resolution(hostname):
    """Verifica la resolución DNS de un hostname"""
    print(f"Verificando resolución DNS para: {hostname}")
    try:
        # Intentar resolver el hostname
        ip_address = socket.gethostbyname(hostname)
        print(f"  Resolución exitosa: {hostname} -> {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"  Error de resolución DNS: {e}")
        return False

def check_srv_records(hostname):
    """Verifica los registros SRV para MongoDB Atlas"""
    print(f"Verificando registros SRV para: _mongodb._tcp.{hostname}")
    try:
        # Intentar resolver los registros SRV
        answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", "SRV")
        print(f"  Registros SRV encontrados: {len(answers)}")
        for rdata in answers:
            print(f"  {rdata.target} (prioridad: {rdata.priority}, peso: {rdata.weight}, puerto: {rdata.port})")
        return True
    except Exception as e:
        print(f"  Error al resolver registros SRV: {e}")
        return False

def test_mongodb_connection(uri):
    """Prueba la conexión a MongoDB con la URI proporcionada"""
    print(f"Probando conexión a MongoDB con URI: {uri[:20]}...")
    
    try:
        # Intentar conectar a MongoDB
        client = pymongo.MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        
        # Forzar una conexión
        server_info = client.server_info()
        
        print(f"  Conexión exitosa a MongoDB")
        print(f"  Versión del servidor: {server_info.get('version', 'desconocida')}")
        
        # Listar bases de datos
        databases = client.list_database_names()
        print(f"  Bases de datos disponibles: {', '.join(databases)}")
        
        return True, None
    except pymongo.errors.ConfigurationError as e:
        return False, f"Error de configuración: {str(e)}"
    except pymongo.errors.ServerSelectionTimeoutError as e:
        return False, f"Timeout al conectar al servidor: {str(e)}"
    except pymongo.errors.OperationFailure as e:
        return False, f"Error de operación (posiblemente credenciales incorrectas): {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

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

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    print_header("VERIFICACIÓN DE CONEXIÓN A MONGODB")
    print(f"Fecha y hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtener la URI de MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    
    if not mongo_uri:
        print("Error: No se encontró la variable de entorno MONGO_URI")
        print("Por favor, asegúrese de que la variable MONGO_URI esté definida en el archivo .env")
        sys.exit(1)
    
    # Extraer el hostname de la URI
    try:
        # Formato típico: mongodb+srv://usuario:contraseña@hostname/basededatos
        hostname = mongo_uri.split("@")[1].split("/")[0]
        print(f"Hostname extraído de la URI: {hostname}")
    except Exception as e:
        print(f"Error al extraer el hostname de la URI: {e}")
        hostname = "cluster0.pmokh.mongodb.net"  # Valor predeterminado basado en los logs
    
    # Verificar resolución DNS
    print_header("VERIFICACIÓN DE DNS")
    dns_ok = check_dns_resolution(hostname)
    
    # Verificar registros SRV para MongoDB Atlas
    srv_ok = check_srv_records(hostname)
    
    # Verificar conectividad de red
    print_header("VERIFICACIÓN DE CONECTIVIDAD DE RED")
    # Probar conectividad a servicios comunes
    check_network_connectivity("8.8.8.8", 53)  # DNS de Google
    check_network_connectivity("1.1.1.1", 53)  # DNS de Cloudflare
    check_network_connectivity("mongodb.com", 443)  # Sitio web de MongoDB
    
    # Probar la conexión a MongoDB
    print_header("PRUEBA DE CONEXIÓN A MONGODB")
    success, error = test_mongodb_connection(mongo_uri)
    
    # Mostrar resultados y recomendaciones
    print_header("RESULTADOS Y RECOMENDACIONES")
    if success:
        print("✅ La conexión a MongoDB fue exitosa")
    else:
        print(f"❌ Error al conectar a MongoDB: {error}")
        
        # Proporcionar recomendaciones basadas en el tipo de error
        if "ConfigurationError" in str(error) or "SRV" in str(error):
            print("\nRecomendaciones:")
            print("1. Verifique que el formato de la URI de MongoDB sea correcto")
            print("2. Asegúrese de que el servidor tenga acceso a Internet para resolver registros DNS")
            print("3. Verifique que no haya restricciones de firewall que bloqueen las conexiones DNS")
            print("4. Intente usar una URI de conexión directa en lugar de SRV")
            
            # Sugerir una URI alternativa sin SRV
            if "mongodb+srv://" in mongo_uri:
                direct_uri = mongo_uri.replace("mongodb+srv://", "mongodb://")
                print(f"\nPruebe con esta URI alternativa (sin SRV):")
                print(f"{direct_uri}")
        
        elif "ServerSelectionTimeoutError" in str(error):
            print("\nRecomendaciones:")
            print("1. Verifique que el servidor tenga acceso a Internet")
            print("2. Asegúrese de que no haya restricciones de firewall que bloqueen las conexiones a MongoDB")
            print("3. Verifique que las direcciones IP del servidor estén en la lista blanca de MongoDB Atlas")
            print("4. Aumente el tiempo de espera de selección del servidor")
        
        elif "OperationFailure" in str(error) or "Authentication failed" in str(error):
            print("\nRecomendaciones:")
            print("1. Verifique que el nombre de usuario y la contraseña sean correctos")
            print("2. Asegúrese de que el usuario tenga los permisos necesarios para acceder a la base de datos")
            print("3. Verifique que la base de datos especificada en la URI exista")
        
        else:
            print("\nRecomendaciones generales:")
            print("1. Verifique la conectividad de red del servidor")
            print("2. Asegúrese de que MongoDB Atlas esté funcionando correctamente")
            print("3. Verifique que la URI de MongoDB sea correcta")
            print("4. Consulte la documentación de MongoDB para obtener más información")

if __name__ == "__main__":
    main()
