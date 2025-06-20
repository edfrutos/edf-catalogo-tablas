#!/usr/bin/env python3
# Script: verificar_estado_db.py
# Descripción: Herramienta para verificar el estado actual de la base de datos
# Uso: python3 verificar_estado_db.py
# Requiere: pymongo, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import os
import sys
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_ssl_cert_path():
    """Obtiene la ruta al certificado SSL del sistema."""
    # Rutas comunes de certificados en diferentes sistemas operativos
    ssl_paths = [
        '/etc/ssl/certs/ca-certificates.crt',  # Ubuntu/Debian
        '/etc/ssl/cert.pem',                   # macOS
        '/etc/pki/tls/certs/ca-bundle.crt',    # RHEL/CentOS
        '/etc/ssl/ca-bundle.pem',              # Otros Linux
    ]
    
    for path in ssl_paths:
        if os.path.exists(path):
            return path
    
    # Si no se encuentra en las rutas comunes, intenta usar el certificado incluido con certifi
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None

def connect_to_mongodb():
    """Establecer conexión segura con MongoDB."""
    try:
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        
        if not mongo_uri:
            logger.error("ERROR: La variable de entorno MONGO_URI no está definida")
            sys.exit(1)
        
        # Obtener la ruta del certificado SSL
        ca_path = get_ssl_cert_path()
        
        if not ca_path or not os.path.exists(ca_path):
            logger.warning("No se pudo encontrar el archivo de certificados CA del sistema")
            logger.warning("Intentando instalar el paquete certifi...")
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "certifi"])
                import certifi
                ca_path = certifi.where()
                logger.info(f"Usando certificados de certifi: {ca_path}")
            except Exception as e:
                logger.error(f"No se pudo instalar certifi: {str(e)}")
                logger.warning("Se intentará la conexión sin verificación de certificado (NO RECOMENDADO EN PRODUCCIÓN)")
                ca_path = None
        
        # Configuración de la conexión
        client_options = {
            'host': mongo_uri,
            'retryWrites': True,
            'w': 'majority',
            'connectTimeoutMS': 10000,
            'socketTimeoutMS': 30000,
            'serverSelectionTimeoutMS': 5000
        }
        
        if ca_path and os.path.exists(ca_path):
            client_options.update({
                'tls': True,
                'tlsCAFile': ca_path,
                'tlsAllowInvalidCertificates': False
            })
            logger.debug(f"Usando certificado CA: {ca_path}")
        else:
            logger.warning("No se encontró archivo de certificados CA. La conexión podría no ser segura.")
            client_options.update({
                'tls': True,
                'tlsAllowInvalidCertificates': True
            })
        
        client = MongoClient(**client_options)
        
        # Verificar conexión
        client.admin.command('ping')
        logger.info("✅ Conexión exitosa con MongoDB")
        logger.info(f"Versión del servidor: {client.server_info()['version']}")
        return client
        
    except Exception as e:
        logger.error(f"❌ Error al conectar a MongoDB: {str(e)}")
        logger.info("Sugerencias de solución de problemas:")
        logger.info("1. Verifica que la variable de entorno MONGO_URI esté correctamente configurada")
        logger.info("2. Asegúrate de tener acceso a internet para la conexión con MongoDB Atlas")
        logger.info("3. Si estás detrás de un proxy o firewall, verifica que permita conexiones a MongoDB")
        logger.info("4. Revisa que el usuario de la base de datos tenga los permisos necesarios")
        sys.exit(1)

def verificar_usuarios(db):
    """Verificar estado de la colección de usuarios."""
    logger.info("\n🔍 Verificando colección 'users'")
    
    try:
        # Contar usuarios
        total_usuarios = db.users.count_documents({})
        logger.info(f"Total de usuarios: {total_usuarios}")
        
        # Verificar usuarios sin username
        usuarios_sin_username = db.users.count_documents({
            '$or': [
                {'username': {'$exists': False}},
                {'username': None},
                {'username': ''}
            ]
        })
        logger.info(f"Usuarios sin username: {usuarios_sin_username}")
        
        # Verificar índices
        indices = db.users.index_information()
        logger.info("Índices en 'users':")
        for nombre, config in indices.items():
            logger.info(f"  - {nombre}: {config['key']}")
            
        # Mostrar algunos usuarios de ejemplo
        logger.info("\nEjemplo de usuarios:")
        for user in db.users.find().limit(3):
            logger.info(f"  - {user.get('username', 'Sin username')} ({user.get('email', 'Sin email')})")
            
        return usuarios_sin_username == 0
        
    except Exception as e:
        logger.error(f"Error al verificar usuarios: {str(e)}")
        return False

def verificar_coleccion_general(db, nombre_coleccion, campos_requeridos=[]):
    """Verificar una colección genérica."""
    logger.info(f"\n🔍 Verificando colección '{nombre_coleccion}'")
    
    try:
        coleccion = db[nombre_coleccion]
        total = coleccion.count_documents({})
        logger.info(f"Total de documentos: {total}")
        
        # Verificar campos requeridos
        if campos_requeridos:
            for campo in campos_requeridos:
                sin_campo = coleccion.count_documents({campo: {'$exists': False}})
                logger.info(f"Documentos sin campo '{campo}': {sin_campo}")
        
        # Verificar índices
        indices = coleccion.index_information()
        logger.info("Índices:")
        for nombre, config in indices.items():
            logger.info(f"  - {nombre}: {config['key']}")
            
        # Mostrar conteo por algún campo relevante si existe
        if total > 0:
            primer_doc = coleccion.find_one()
            if primer_doc and 'status' in primer_doc:
                pipeline = [
                    {'$group': {'_id': f'${campo}', 'count': {'$sum': 1}}} for campo in ['status']
                ]
                for doc in coleccion.aggregate(pipeline):
                    logger.info(f"  - {doc['_id']}: {doc['count']} documentos")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al verificar {nombre_coleccion}: {str(e)}")
        return False

def main():
    """Función principal."""
    logger.info("="*70)
    logger.info("VERIFICACIÓN DE ESTADO DE LA BASE DE DATOS".center(70))
    logger.info("="*70)
    
    try:
        # Conectar a MongoDB
        client = connect_to_mongodb()
        db = client.get_database()
        
        # Verificar colecciones
        todo_ok = True
        
        # Verificar usuarios
        if not verificar_usuarios(db):
            todo_ok = False
            
        # Verificar catálogos
        if not verificar_coleccion_general(
            db, 
            'catalogs', 
            ['name', 'owner_id', 'created_at']
        ):
            todo_ok = False
            
        # Verificar hojas de cálculo
        if not verificar_coleccion_general(
            db,
            'spreadsheet',
            ['file_id', 'uploaded_by', 'uploaded_at']
        ):
            todo_ok = False
            
        # Verificar logs de auditoría
        if not verificar_coleccion_general(
            db,
            'audit_logs',
            ['user_id', 'action', 'timestamp']
        ):
            todo_ok = False
        
        # Mostrar resumen
        logger.info("\n" + "="*70)
        if todo_ok:
            logger.info("✅ Verificación completada con éxito")
        else:
            logger.warning("⚠️ Se encontraron problemas durante la verificación")
        logger.info("="*70)
        
        return 0 if todo_ok else 1
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return 1
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    sys.exit(main())
