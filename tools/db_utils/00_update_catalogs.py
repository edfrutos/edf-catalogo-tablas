#!/usr/bin/env python3
# Script: 00_update_catalogs.py
# Descripción: Herramienta para actualizar catálogos en la base de datos MongoDB.
#             Permite actualizar campos específicos en múltiples documentos de forma segura.
# Uso: python3 00_update_catalogs.py [--collection COLLECTION] [--query QUERY] --update UPDATE [--dry-run] [--limit LIMIT]
# Opciones:
#   --collection COLLECTION  Nombre de la colección a actualizar (default: 'catalogs')
#   --query QUERY           Filtro de búsqueda en formato JSON (default: '{}')
#   --update UPDATE         Actualización a aplicar en formato JSON (requerido)
#   --dry-run               Mostrar cambios sin aplicarlos
#   --limit LIMIT           Límite de documentos a actualizar (default: sin límite)
# Requiere: pymongo, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import os
import json
import logging
import argparse
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util
from datetime import datetime
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parsear argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Actualiza documentos en una colección de MongoDB')
    parser.add_argument('--collection', default='catalogs', help='Nombre de la colección')
    parser.add_argument('--query', default='{}', help='Filtro de búsqueda en formato JSON')
    parser.add_argument('--update', required=True, help='Actualización a aplicar en formato JSON')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar cambios sin aplicarlos')
    parser.add_argument('--limit', type=int, default=0, help='Límite de documentos a actualizar')
    return parser.parse_args()

def connect_to_mongodb():
    """Establecer conexión con MongoDB."""
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        raise ValueError('La variable de entorno MONGO_URI no está definida')
    
    try:
        client = MongoClient(mongo_uri)
        # Verificar la conexión
        client.admin.command('ping')
        return client
    except Exception as e:
        logger.error(f'Error al conectar a MongoDB: {str(e)}')
        raise

def validate_json(json_str, name):
    """Validar y parsear cadena JSON."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f'Error al parsear {name}: {str(e)}')
        raise

def main():
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Validar y parsear consultas
        query = validate_json(args.query, 'consulta')
        update = validate_json(args.update, 'actualización')
        
        # Conectar a MongoDB
        client = connect_to_mongodb()
        db = client.get_database()
        collection = db[args.collection]
        
        # Contar documentos que coinciden
        count = collection.count_documents(query)
        logger.info(f'Encontrados {count} documentos que coinciden con la consulta')
        
        if count == 0:
            logger.warning('No se encontraron documentos que coincidan con la consulta')
            return
            
        # Configurar límite
        limit = args.limit if args.limit > 0 else count
        
        # Ejecutar actualización
        if args.dry_run:
            logger.info('=== MODO SIMULACIÓN (dry-run) ===')
            logger.info('Se actualizarían los siguientes documentos:')
            
            # Mostrar ejemplos
            sample_docs = list(collection.find(query).limit(min(3, limit)))
            for doc in sample_docs:
                logger.info(f'  - {doc["_id"]}: {json.dumps(doc, default=str, indent=2)}')
                logger.info(f'    Actualización: {update}')
            
            logger.info(f'\nTotal de documentos a actualizar: {min(limit, count)}')
        else:
            # Aplicar actualización
            logger.info(f'Iniciando actualización de hasta {limit} documentos...')
            
            # Usar bulk operations para mejor rendimiento
            bulk = collection.initialize_unordered_bulk_op()
            updated_count = 0
            
            for doc in collection.find(query).limit(limit):
                bulk.find({'_id': doc['_id']}).update({'$set': update})
                updated_count += 1
                
                # Ejecutar en lotes de 1000
                if updated_count % 1000 == 0:
                    bulk.execute()
                    logger.info(f'Actualizados {updated_count} documentos...')
                    bulk = collection.initialize_unordered_bulk_op()
            
            # Ejecutar operaciones restantes
            if updated_count % 1000 != 0:
                bulk.execute()
            
            logger.info(f'Actualización completada. Total de documentos actualizados: {updated_count}')
            
            # Registrar en log de auditoría
            audit_log = {
                'timestamp': datetime.utcnow(),
                'action': 'update_catalogs',
                'collection': args.collection,
                'query': query,
                'update': update,
                'documents_updated': updated_count,
                'dry_run': False
            }
            
            try:
                db.audit_logs.insert_one(audit_log)
            except Exception as e:
                logger.error(f'Error al registrar en log de auditoría: {str(e)}')
    
    except Exception as e:
        logger.error(f'Error en la ejecución: {str(e)}', exc_info=True)
        raise
    finally:
        if 'client' in locals():
            client.close()

if __name__ == '__main__':
    main()
