#!/usr/bin/env python3
from flask import Flask
from pymongo import MongoClient
from bson import ObjectId, errors
import os
import logging
import sys
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crear una aplicación Flask mínima
app = Flask(__name__)

# Configuración de MongoDB
MONGO_URI = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"
db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[db_name]

def is_valid_object_id(id_str):
    """Verifica si una cadena es un ObjectId válido"""
    try:
        ObjectId(id_str)
        return True
    except (errors.InvalidId, TypeError):
        return False

def check_catalog_exists(catalog_id=None):
    """Busca un catálogo en todas las colecciones disponibles"""
    if not catalog_id:
        # Si no se proporciona un ID, usar el ID problemático del log
        catalog_id = "67f7ff96fd762aa1411f7803"
        
    logger.info(f"Buscando catálogo con ID: {catalog_id}")
    logger.info(f"¿Es un ObjectId válido? {is_valid_object_id(catalog_id)}")
    
    # Comprobar en la colección catalogs
    if is_valid_object_id(catalog_id):
        try:
            catalog = db.catalogs.find_one({"_id": ObjectId(catalog_id)})
            if catalog:
                logger.info(f"Catálogo encontrado en la colección 'catalogs' con ObjectId: {catalog}")
                return catalog
        except Exception as e:
            logger.error(f"Error al buscar en catalogs por ObjectId: {str(e)}")
    
    # Comprobar en la colección spreadsheets
    if is_valid_object_id(catalog_id):
        try:
            catalog = db.spreadsheets.find_one({"_id": ObjectId(catalog_id)})
            if catalog:
                logger.info(f"Catálogo encontrado en la colección 'spreadsheets' con ObjectId: {catalog}")
                return catalog
        except Exception as e:
            logger.error(f"Error al buscar en spreadsheets por ObjectId: {str(e)}")
    
    # Comprobar si existe como string en lugar de ObjectId
    try:
        catalog = db.catalogs.find_one({"_id": catalog_id})
        if catalog:
            logger.info(f"Catálogo encontrado en 'catalogs' con _id como string: {catalog}")
            return catalog
    except Exception as e:
        logger.error(f"Error al buscar en catalogs por string: {str(e)}")
    
    try:
        catalog = db.spreadsheets.find_one({"_id": catalog_id})
        if catalog:
            logger.info(f"Catálogo encontrado en 'spreadsheets' con _id como string: {catalog}")
            return catalog
    except Exception as e:
        logger.error(f"Error al buscar en spreadsheets por string: {str(e)}")
    
    # Buscar por nombre que coincida con el ID
    try:
        catalog = db.catalogs.find_one({"name": catalog_id})
        if catalog:
            logger.info(f"Catálogo encontrado en 'catalogs' por nombre: {catalog}")
            return catalog
    except Exception as e:
        logger.error(f"Error al buscar en catalogs por nombre: {str(e)}")
    
    try:
        catalog = db.spreadsheets.find_one({"name": catalog_id})
        if catalog:
            logger.info(f"Catálogo encontrado en 'spreadsheets' por nombre: {catalog}")
            return catalog
    except Exception as e:
        logger.error(f"Error al buscar en spreadsheets por nombre: {str(e)}")
    
    # Buscar en todas las colecciones para ver si el catálogo existe en otra colección
    collections = db.list_collection_names()
    logger.info(f"Colecciones disponibles: {collections}")
    
    for collection_name in collections:
        if collection_name not in ['catalogs', 'spreadsheets']:
            collection = db[collection_name]
            if is_valid_object_id(catalog_id):
                try:
                    catalog = collection.find_one({"_id": ObjectId(catalog_id)})
                    if catalog:
                        logger.info(f"Catálogo encontrado en la colección '{collection_name}' con ObjectId: {catalog}")
                        return catalog
                except Exception as e:
                    logger.error(f"Error al buscar en {collection_name} por ObjectId: {str(e)}")
            
            try:
                catalog = collection.find_one({"_id": catalog_id})
                if catalog:
                    logger.info(f"Catálogo encontrado en la colección '{collection_name}' con _id como string: {catalog}")
                    return catalog
            except Exception as e:
                logger.error(f"Error al buscar en {collection_name} por string: {str(e)}")
    
    # Buscar IDs similares para depuración
    try:
        all_catalogs_ids = []
        for collection_name in ['catalogs', 'spreadsheets']:
            collection = db[collection_name]
            catalogs = list(collection.find({}, {"_id": 1, "name": 1}).limit(20))
            for cat in catalogs:
                all_catalogs_ids.append({
                    "collection": collection_name,
                    "id": str(cat["_id"]),
                    "name": cat.get("name", "Sin nombre")
                })
        
        logger.info(f"IDs de catálogos disponibles (hasta 20): {json.dumps(all_catalogs_ids, indent=2)}")
        
        # Verificar si hay algún catálogo con un ID similar
        similar_ids = [item for item in all_catalogs_ids if catalog_id in item["id"] or item["id"] in catalog_id]
        if similar_ids:
            logger.info(f"IDs similares encontrados: {similar_ids}")
    except Exception as e:
        logger.error(f"Error al listar catálogos disponibles: {str(e)}")
    
    # Si llegamos aquí, el catálogo no existe
    logger.error(f"Catálogo con ID {catalog_id} no encontrado en ninguna colección")
    return None

def list_all_collections_info():
    """Lista información sobre todas las colecciones en la base de datos"""
    collections = db.list_collection_names()
    logger.info(f"Total de colecciones: {len(collections)}")
    
    for collection_name in collections:
        try:
            count = db[collection_name].count_documents({})
            logger.info(f"Colección '{collection_name}': {count} documentos")
            
            # Mostrar algunos ejemplos de documentos para las colecciones principales
            if collection_name in ['catalogs', 'spreadsheets'] and count > 0:
                sample = list(db[collection_name].find().limit(3))
                for doc in sample:
                    doc_id = str(doc.get('_id', 'Sin ID'))
                    doc_name = doc.get('name', 'Sin nombre')
                    doc_owner = doc.get('owner', doc.get('created_by', 'Sin propietario'))
                    logger.info(f"  Ejemplo: ID={doc_id}, Nombre={doc_name}, Propietario={doc_owner}")
        except Exception as e:
            logger.error(f"Error al obtener información de la colección '{collection_name}': {str(e)}")

def fix_catalog_permissions():
    """Corrige los permisos de los catálogos que no tienen el campo created_by"""
    collections = ['catalogs', 'spreadsheets']
    fixed_count = 0
    
    for collection_name in collections:
        collection = db[collection_name]
        # Buscar documentos sin el campo created_by
        missing_created_by = collection.find({"created_by": {"$exists": False}})
        
        for doc in missing_created_by:
            doc_id = str(doc.get('_id', 'Sin ID'))
            owner = doc.get('owner', 'admin@example.com')
            owner_name = doc.get('owner_name')
            
            update_data = {"created_by": owner_name if owner_name else owner}
            
            try:
                result = collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
                if result.modified_count > 0:
                    fixed_count += 1
                    logger.info(f"Corregido documento {doc_id} en {collection_name}, añadido created_by={update_data['created_by']}")
            except Exception as e:
                logger.error(f"Error al actualizar documento {doc_id} en {collection_name}: {str(e)}")
    
    logger.info(f"Total de documentos corregidos: {fixed_count}")

def main():
    """Función principal que ejecuta las tareas de diagnóstico y corrección"""
    logger.info("=== INICIANDO DIAGNÓSTICO DE CATÁLOGOS ===")
    
    # Listar información de todas las colecciones
    logger.info("\n=== INFORMACIÓN DE COLECCIONES ===")
    list_all_collections_info()
    
    # Buscar catálogos específicos mencionados en los logs de error
    logger.info("\n=== BÚSQUEDA DE CATÁLOGOS PROBLEMÁTICOS ===")
    problem_ids = ["67f7ff96fd762aa1411f7803", "6824d9cc252f62f5e5350f62"]
    
    for catalog_id in problem_ids:
        logger.info(f"\nBuscando catálogo: {catalog_id}")
        check_catalog_exists(catalog_id)
    
    # Corregir permisos de catálogos
    logger.info("\n=== CORRECCIÓN DE PERMISOS DE CATÁLOGOS ===")
    fix_catalog_permissions()
    
    logger.info("\n=== DIAGNÓSTICO COMPLETADO ===")

if __name__ == "__main__":
    main()
