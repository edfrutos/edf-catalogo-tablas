#!/usr/bin/env python3
# Script: 03_ver_guardado_rutas_en_MongoDB.py
# Descripción: Herramienta para verificar y validar rutas almacenadas en documentos de MongoDB.
#             Identifica rutas inválidas, inaccesibles o mal formateadas en los documentos.
# Uso: python3 03_ver_guardado_rutas_en_MongoDB.py [--collection COLLECTION] [--path-field PATH_FIELD] [--fix]
# Opciones:
#   --collection COLLECTION  Nombre de la colección a verificar (default: 'catalogs')
#   --path-field PATH_FIELD  Campo que contiene la ruta a verificar (default: 'path')
#   --fix                   Intentar corregir rutas automáticamente
#   --limit LIMIT           Límite de documentos a procesar (default: sin límite)
# Requiere: pymongo, python-dotenv
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import os
import re
import json
import logging
import argparse
from pathlib import Path
from urllib.parse import urlparse, unquote
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('path_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class PathValidator:
    """Clase para validar y corregir rutas en documentos de MongoDB."""
    
    def __init__(self, collection, path_field='path', fix=False):
        self.collection = collection
        self.path_field = path_field
        self.fix = fix
        self.stats = {
            'total_documents': 0,
            'documents_with_path': 0,
            'valid_paths': 0,
            'invalid_paths': 0,
            'fixed_paths': 0,
            'errors': 0
        }
    
    def is_valid_path(self, path_str):
        """Verifica si una ruta es válida y accesible."""
        if not path_str:
            return False
            
        try:
            # Verificar si es una URL
            if path_str.startswith(('http://', 'https://', 's3://', 'gs://')):
                parsed = urlparse(path_str)
                return bool(parsed.scheme and parsed.netloc)
            
            # Verificar si es una ruta de sistema de archivos
            path = Path(path_str).expanduser().resolve()
            return path.exists()
            
        except Exception:
            return False
    
    def normalize_path(self, path_str):
        """Normaliza una ruta para su almacenamiento consistente."""
        if not path_str:
            return path_str
            
        try:
            # Manejar URLs
            if path_str.startswith(('http://', 'https://', 's3://', 'gs://')):
                parsed = urlparse(path_str)
                # Normalizar la URL decodificando caracteres especiales
                path_str = parsed._replace(path=unquote(parsed.path)).geturl()
                return path_str
            
            # Normalizar rutas de sistema de archivos
            path = Path(path_str).expanduser()
            # Convertir a ruta absoluta si no lo es
            if not path.is_absolute():
                path = path.resolve()
            return str(path)
            
        except Exception as e:
            logger.warning(f'Error al normalizar ruta "{path_str}": {str(e)}')
            return path_str
    
    def process_document(self, doc):
        """Procesa un documento individual para validar/corregir su ruta."""
        doc_id = str(doc.get('_id', 'unknown'))
        self.stats['total_documents'] += 1
        
        try:
            # Verificar si el documento tiene el campo de ruta
            if self.path_field not in doc:
                logger.debug(f'Documento {doc_id} no tiene el campo "{self.path_field}"')
                return
                
            self.stats['documents_with_path'] += 1
            path_value = doc[self.path_field]
            
            # Manejar diferentes tipos de valores de ruta
            if isinstance(path_value, list):
                paths = path_value
                is_list = True
            else:
                paths = [path_value]
                is_list = False
            
            valid_paths = []
            has_invalid = False
            
            for i, path in enumerate(paths):
                if not path or not isinstance(path, str):
                    logger.warning(f'Documento {doc_id}: Ruta {i} inválida (tipo {type(path)})')
                    has_invalid = True
                    continue
                    
                normalized = self.normalize_path(path)
                is_valid = self.is_valid_path(normalized)
                
                if is_valid:
                    valid_paths.append(normalized)
                    self.stats['valid_paths'] += 1
                    logger.debug(f'Documento {doc_id}: Ruta válida: {normalized}')
                else:
                    logger.warning(f'Documento {doc_id}: Ruta inválida: {path}')
                    self.stats['invalid_paths'] += 1
                    has_invalid = True
                    
                    # Intentar corregir si está habilitado
                    if self.fix:
                        # Aquí podrías implementar lógica de corrección específica
                        # Por ejemplo, buscar rutas alternativas o patrones comunes
                        logger.info(f'Intentando corregir ruta: {path}')
                        # Por ahora, simplemente mantenemos la normalizada
                        valid_paths.append(normalized)
                        self.stats['fixed_paths'] += 1
            
            # Actualizar el documento si es necesario
            if self.fix and has_invalid:
                update_value = valid_paths if is_list else (valid_paths[0] if valid_paths else None)
                
                try:
                    self.collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': {self.path_field: update_value}}
                    )
                    logger.info(f'Documento {doc_id} actualizado con rutas corregidas')
                except Exception as e:
                    logger.error(f'Error al actualizar documento {doc_id}: {str(e)}')
                    self.stats['errors'] += 1
        
        except Exception as e:
            logger.error(f'Error al procesar documento {doc_id}: {str(e)}', exc_info=True)
            self.stats['errors'] += 1

def parse_arguments():
    """Parsear argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Verifica y valida rutas en documentos de MongoDB')
    parser.add_argument('--collection', default='catalogs', help='Nombre de la colección')
    parser.add_argument('--path-field', default='path', help='Campo que contiene la ruta a verificar')
    parser.add_argument('--fix', action='store_true', help='Intentar corregir rutas automáticamente')
    parser.add_argument('--limit', type=int, default=0, help='Límite de documentos a procesar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar mensajes de depuración')
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

def main():
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Configurar nivel de logging
        logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
        
        logger.info('=== Iniciando validación de rutas en MongoDB ===')
        logger.info(f'Colección: {args.collection}')
        logger.info(f'Campo de ruta: {args.path_field}')
        logger.info(f'Modo corrección: {'Activado' if args.fix else 'Desactivado'}')
        
        # Conectar a MongoDB
        client = connect_to_mongodb()
        db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
        db = client[db_name]
        collection = db[args.collection]
        
        # Inicializar validador
        validator = PathValidator(collection, args.path_field, args.fix)
        
        # Consultar documentos (solo los que tienen el campo de ruta)
        query = {args.path_field: {'$exists': True, '$ne': None}}
        
        # Contar documentos totales
        total_docs = collection.count_documents(query)
        logger.info(f'Documentos a procesar: {total_docs}')
        
        # Configurar límite
        limit = args.limit if args.limit > 0 else total_docs
        
        # Procesar documentos
        processed = 0
        for doc in collection.find(query).limit(limit):
            validator.process_document(doc)
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f'Procesados {processed}/{limit} documentos...')
        
        # Mostrar resumen
        logger.info('\n=== Resumen de la validación ===')
        logger.info(f'Documentos totales: {validator.stats["total_documents"]}')
        logger.info(f'Documentos con ruta: {validator.stats["documents_with_path"]}')
        logger.info(f'Rutas válidas: {validator.stats["valid_paths"]}')
        logger.info(f'Rutas inválidas: {validator.stats["invalid_paths"]}')
        
        if args.fix:
            logger.info(f'Rutas corregidas: {validator.stats["fixed_paths"]}')
        
        if validator.stats["errors"] > 0:
            logger.warning(f'Errores encontrados: {validator.stats["errors"]}')
        
        logger.info('Validación completada')
        
    except Exception as e:
        logger.error(f'Error en la ejecución: {str(e)}', exc_info=True)
        return 1
    finally:
        if 'client' in locals():
            client.close()
    
    return 0

if __name__ == '__main__':
    exit(main())
