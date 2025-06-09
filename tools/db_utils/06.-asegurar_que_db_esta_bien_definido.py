#!/usr/bin/env python3
# Script: 06.-asegurar_que_db_esta_bien_definido.py
# Descripción: Herramienta para verificar la configuración básica de la base de datos
# Uso: python3 06.-asegurar_que_db_esta_bien_definido.py
# Requiere: pymongo, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import os
import sys
import logging
import argparse
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_check.log')
    ]
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
            raise ValueError('La variable de entorno MONGO_URI no está definida')
        
        # Obtener la ruta del certificado SSL del sistema
        ca_cert_path = get_ssl_cert_path()
        
        if not ca_cert_path or not os.path.exists(ca_cert_path):
            logger.warning("No se encontró el archivo de certificados CA del sistema")
            logger.info("Instalando certificados del sistema...")
            try:
                # Intentar instalar certificados en sistemas basados en Debian/Ubuntu
                if os.path.exists('/etc/debian_version'):
                    os.system('sudo apt-get update && sudo apt-get install -y ca-certificates')
                    ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
            except Exception as e:
                logger.warning(f"No se pudieron instalar los certificados: {str(e)}")
        
        # Configuración segura para producción
        client_options = {
            'tls': True,
            'tlsCAFile': ca_cert_path,  # Usar certificados del sistema
            'tlsAllowInvalidCertificates': False,  # Verificación estricta de certificados
            'tlsAllowInvalidHostnames': False,     # Verificación estricta de nombres de host
            'serverSelectionTimeoutMS': 10000,     # 10 segundos de timeout
            'connectTimeoutMS': 10000,
            'retryWrites': True,
            'w': 'majority',
            'readPreference': 'secondaryPreferred'  # Mejorar disponibilidad de lectura
        }
        
        # Crear el cliente con las opciones de conexión segura
        client = MongoClient(mongo_uri, **client_options)
        
        # Verificar la conexión con un comando simple
        client.admin.command('ping')
        logger.info("Conexión segura establecida con MongoDB Atlas")
        
        # Verificar versión del servidor
        server_info = client.server_info()
        logger.info(f"Conectado a MongoDB v{server_info.get('version')}")
        
        return client
        
    except Exception as e:
        logger.error(f"Error al conectar a MongoDB: {str(e)}")
        if 'certificate verify failed' in str(e):
            logger.error("Error de verificación de certificado SSL")
            logger.info("Soluciones posibles:")
            logger.info("1. Asegúrate de tener los certificados CA instalados")
            logger.info("2. Verifica que la fecha y hora del sistema sean correctas")
            logger.info("3. Si estás detrás de un proxy, configura las variables de entorno HTTP_PROXY/HTTPS_PROXY")
        
        logger.warning("Verifica también que:")
        logger.warning("1. La variable MONGO_URI en .env sea correcta")
        logger.warning("2. Tu IP esté en la lista blanca de MongoDB Atlas")
        logger.warning("3. El usuario de la base de datos tenga los permisos necesarios")
        sys.exit(1)

def check_collections(db):
    """Verificar colecciones existentes y sus índices."""
    logger.info("\n=== Verificando colecciones e índices ===")
    
    # Definición de colecciones esperadas y sus índices
    expected_collections = {
        'users': {
            'description': 'Usuarios del sistema',
            'indexes': [
                {'keys': [('email', 1)], 'unique': True, 'name': 'email_unique'},
                {'keys': [('username', 1)], 'unique': True, 'name': 'username_unique'},
                {'keys': [('created_at', -1)], 'name': 'created_at_desc'}
            ]
        },
        'catalogs': {
            'description': 'Catálogos principales',
            'indexes': [
                {'keys': [('name', 1)], 'name': 'name_index'},
                {'keys': [('owner_id', 1)], 'name': 'owner_id_index'},
                {'keys': [('created_at', -1)], 'name': 'created_at_desc'}
            ]
        },
        'spreadsheet': {
            'description': 'Hojas de cálculo importadas',
            'indexes': [
                {'keys': [('file_id', 1)], 'unique': True, 'name': 'file_id_unique'},
                {'keys': [('uploaded_by', 1)], 'name': 'uploaded_by_index'},
                {'keys': [('uploaded_at', -1)], 'name': 'uploaded_at_desc'}
            ]
        },
        'audit_logs': {
            'description': 'Registros de auditoría',
            'indexes': [
                {'keys': [('timestamp', -1)], 'name': 'timestamp_desc'},
                {'keys': [('user_id', 1)], 'name': 'user_id_index'},
                {'keys': [('action', 1)], 'name': 'action_index'}
            ]
        }
    }
    
    all_ok = True
    existing_collections = set(db.list_collection_names())
    
    for col_name, col_config in expected_collections.items():
        logger.info(f"\nVerificando colección: {col_name} - {col_config['description']}")
        
        # Verificar si la colección existe
        if col_name not in existing_collections:
            logger.warning(f"  ✗ La colección '{col_name}' no existe")
            all_ok = False
            
            # Crear la colección si no existe y está habilitado el modo fix
            if hasattr(args, 'fix') and args.fix:
                try:
                    db.create_collection(col_name)
                    logger.info(f"  ✓ Colección '{col_name}' creada exitosamente")
                    existing_collections.add(col_name)
                except Exception as e:
                    logger.error(f"  ✗ Error al crear la colección '{col_name}': {str(e)}")
                    continue
        else:
            logger.info(f"  ✓ La colección existe")
        
        # Verificar índices
        if col_name in existing_collections and 'indexes' in col_config:
            collection = db[col_name]
            existing_indexes = {idx['name']: idx['key'] 
                             for idx in collection.list_indexes() 
                             if idx['name'] != '_id_'}
            
            for idx_config in col_config['indexes']:
                idx_name = idx_config['name']
                idx_keys = list((k, v) for k, v in idx_config['keys'])
                
                if idx_name not in existing_indexes:
                    logger.warning(f"  ✗ Falta índice: {idx_name} ({idx_keys})")
                    all_ok = False
                    
                    # Crear el índice si está habilitado el modo fix
                    if hasattr(args, 'fix') and args.fix:
                        try:
                            if idx_name == 'username_unique':
                                # Primero, limpiar valores nulos o vacíos en username
                                # Generar usernames únicos basados en el email o en un contador
                                users_without_username = list(collection.find({
                                    '$or': [
                                        {'username': {'$exists': False}},
                                        {'username': None},
                                        {'username': ''},
                                        {'username': {'$type': 'null'}}
                                    ]
                                }))
                                
                                for i, user in enumerate(users_without_username, 1):
                                    new_username = None
                                    if 'email' in user and user['email']:
                                        # Usar la parte antes del @ del email como base
                                        email_base = user['email'].split('@')[0]
                                        new_username = email_base.lower()
                                    else:
                                        # Si no hay email, usar un prefijo genérico
                                        new_username = f'user_{i}'
                                    
                                    # Asegurarse de que el username sea único
                                    counter = 1
                                    base_username = new_username
                                    while collection.count_documents({'username': new_username}) > 0:
                                        new_username = f"{base_username}_{counter}"
                                        counter += 1
                                    
                                    # Actualizar el documento
                                    collection.update_one(
                                        {'_id': user['_id']},
                                        {'$set': {'username': new_username}}
                                    )
                                
                                # Ahora que todos los usuarios tienen username, crear el índice único
                                collection.create_index([('username', 1)], unique=True, name='username_unique')
                                logger.info(f"  ✓ Índice creado: username_unique")
                                logger.info(f"  ✓ Se actualizaron {len(users_without_username)} usuarios sin username")
                                
                            else:
                                collection.create_index(idx_keys, name=idx_name, unique=idx_config.get('unique', False))
                                logger.info(f"  ✓ Índice creado: {idx_name}")
                        except Exception as e:
                            logger.error(f"  ✗ Error al crear índice {idx_name}: {str(e)}")
                            all_ok = False
                else:
                    logger.info(f"  ✓ Índice existe: {idx_name}")
    
    if all_ok:
        logger.info("\nTodas las colecciones e índices están correctamente configurados")
    else:
        logger.warning("\nSe encontraron problemas en la configuración de las colecciones")
        if not hasattr(args, 'fix') or not args.fix:
            logger.info("Ejecuta con --fix para corregir automáticamente los problemas")
    
    return all_ok

def check_indexes(db):
    """Verificar índices importantes."""
    logger.info("\n=== Verificando índices ===")
    
    # Índices esperados por colección
    expected_indexes = {
        'users': [
            [('email', ASCENDING)],
            [('username', ASCENDING)]
        ],
        'catalogs': [
            [('owner_id', ASCENDING)],
            [('created_at', DESCENDING)]
        ],
        'audit_logs': [
            [('timestamp', DESCENDING)]
        ]
    }
    
    all_ok = True
    
    for collection_name, indexes in expected_indexes.items():
        try:
            collection = db[collection_name]
            existing_indexes = [idx['key'] for idx in collection.list_indexes()]
            
            for idx in indexes:
                if idx not in existing_indexes:
                    logger.warning(f"Falta índice en {collection_name}: {idx}")
                    all_ok = False
                    
        except Exception as e:
            logger.error(f"Error al verificar índices de {collection_name}: {str(e)}")
            all_ok = False
    
    if all_ok:
        logger.info("Todos los índices necesarios existen")
    
    return all_ok

def check_database_health(db):
    """Verificar el estado general de la base de datos."""
    logger.info("\n=== Verificando estado de la base de datos ===")
    
    try:
        # Obtener estadísticas de la base de datos
        stats = db.command('dbstats')
        
        logger.info(f"Nombre de la base de datos: {db.name}")
        logger.info(f"Colecciones: {stats['collections']}")
        logger.info(f"Documentos: {stats['objects']}")
        logger.info(f"Tamaño de datos: {stats['dataSize'] / (1024*1024):.2f} MB")
        logger.info(f"Tamaño de almacenamiento: {stats['storageSize'] / (1024*1024):.2f} MB")
        
        return True
    except Exception as e:
        logger.error(f"Error al verificar el estado de la base de datos: {str(e)}")
        return False

def parse_arguments():
    """Parsear argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Verificar y reparar la configuración de la base de datos')
    parser.add_argument('--fix', action='store_true', help='Aplicar correcciones automáticamente')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    return parser.parse_args()

def print_header():
    """Mostrar encabezado del script."""
    logger.info("=" * 70)
    logger.info("VERIFICACIÓN DE CONFIGURACIÓN DE BASE DE DATOS".center(70))
    logger.info("=" * 70)
    logger.info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 70)

def print_footer(exit_code):
    """Mostrar pie de página del script."""
    logger.info("-" * 70)
    if exit_code == 0:
        logger.info("✅ Verificación completada con éxito")
    else:
        logger.error("❌ Se encontraron problemas durante la verificación")
    logger.info("=" * 70 + "\n")

def main():
    """Función principal."""
    global args
    args = parse_arguments()
    
    # Configurar nivel de log
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        # Mostrar solo mensajes de nivel INFO y superiores
        logger.setLevel(logging.INFO)
        
    print_header()
    logger.info("Iniciando verificación de la base de datos...")
    
    if args.fix:
        logger.warning("MODO REPARACIÓN ACTIVADO - Se aplicarán cambios automáticamente")
    
    client = None
    try:
        # Conectar a MongoDB
        client = connect_to_mongodb()
        db = client.get_database()
        
        # Realizar verificaciones
        logger.info("\n" + "="*30 + " INICIO DE VERIFICACIÓN " + "="*30)
        
        # Verificar colecciones e índices
        collections_ok = check_collections(db)
        
        # Verificar índices adicionales (para compatibilidad)
        indexes_ok = check_indexes(db)
        
        # Verificar estado general de la base de datos
        db_health_ok = check_database_health(db)
        
        # Mostrar resumen
        logger.info("\n" + "="*30 + " RESUMEN DE VERIFICACIÓN " + "="*30)
        
        # Tabla de resumen
        summary = [
            ["Verificación", "Estado", "Detalles"],
            ["-"*20, "-"*10, "-"*30],
            ["Conexión a MongoDB", "✅ OK", "Conexión segura establecida"],
            [
                "Colecciones e índices", 
                "✅ OK" if collections_ok and indexes_ok else "⚠️ PROBLEMAS",
                "Ver arriba para más detalles"
            ],
            [
                "Estado general de la BD", 
                "✅ OK" if db_health_ok else "⚠️ VERIFICAR",
                "Ver arriba para más detalles"
            ]
        ]
        
        # Imprimir tabla de resumen
        for row in summary:
            logger.info("{:<25} {:<12} {}".format(*row))
        
        logger.info("\nNotas:")
        if not all([collections_ok, indexes_ok, db_health_ok]) and not args.fix:
            logger.info("- Ejecuta con --fix para corregir automáticamente los problemas detectados")
        logger.info("- Revisa el archivo db_check.log para ver el registro completo")
        
        return 0 if all([collections_ok, indexes_ok, db_health_ok]) else 1
            
    except Exception as e:
        logger.error(f"\n❌ Error durante la verificación: {str(e)}", exc_info=args.verbose)
        return 1
    finally:
        if client:
            try:
                client.close()
                logger.debug("Conexión a MongoDB cerrada correctamente")
            except Exception as e:
                logger.warning(f"Error al cerrar la conexión: {str(e)}")
        print_footer(0 if 'collections_ok' in locals() and collections_ok and indexes_ok and db_health_ok else 1)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.error("\nOperación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nError inesperado: {str(e)}", exc_info=True)
        sys.exit(1)
