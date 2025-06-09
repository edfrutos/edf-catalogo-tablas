#!/usr/bin/env python3
"""
Script mejorado para limpieza de imágenes no utilizadas
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse
from PIL import Image
import imagehash
from pymongo import MongoClient
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean_images.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageCleaner:
    def __init__(self, config_file='clean_images_config.json'):
        """Inicializar limpiador de imágenes"""
        self.config = self._load_config(config_file)
        self.image_dirs = self.config.get('image_dirs', [])
        self.extensions = self.config.get('extensions', ['.jpg', '.jpeg', '.png', '.gif'])
        self.min_file_size = self.config.get('min_file_size', 1024)  # 1KB
        self.max_file_size = self.config.get('max_file_size', 10 * 1024 * 1024)  # 10MB
        self.min_dimension = self.config.get('min_dimension', 50)  # 50x50 píxeles
        self.dry_run = False
        
        # Conexión a MongoDB
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MONGO_DB', 'catalogotablas')
        self.db = self._connect_mongodb()
        
    def _load_config(self, config_file):
        """Cargar configuración desde archivo JSON"""
        try:
            with open(config_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración {config_file} no encontrado. Usando valores por defecto.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar el archivo de configuración {config_file}")
            return {}

    def _connect_mongodb(self):
        """Conectar a MongoDB"""
        try:
            client = MongoClient(self.mongo_uri)
            # Verificar conexión
            client.admin.command('ping')
            logger.info("Conexión exitosa a MongoDB")
            return client[self.db_name]
        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {str(e)}")
            sys.exit(1)

    def is_image_used(self, image_path):
        """Verificar si una imagen está siendo utilizada en la base de datos"""
        try:
            # Calcular hash de la imagen
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
            
            # Buscar en colecciones que puedan contener referencias a imágenes
            collections_to_check = ['catalogs', 'users', 'products']  # Ajustar según tu esquema
            
            for collection_name in collections_to_check:
                collection = self.db[collection_name]
                
                # Buscar en campos que puedan contener rutas de imágenes
                for field in ['image', 'avatar', 'photo', 'logo', 'images']:
                    query = {field: {'$regex': str(image_path), '$options': 'i'}}
                    if collection.count_documents(query) > 0:
                        return True
                        
                # Buscar por hash
                query = {'image_hash': image_hash}
                if collection.count_documents(query) > 0:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error al verificar uso de imagen {image_path}: {str(e)}")
            return True  # Por defecto, asumir que está en uso para evitar eliminaciones accidentales

    def is_valid_image(self, file_path):
        """Verificar si un archivo es una imagen válida"""
        try:
            with Image.open(file_path) as img:
                # Verificar dimensiones mínimas
                if img.width < self.min_dimension or img.height < self.min_dimension:
                    return False
                    
                # Verificar proporción de aspecto
                aspect_ratio = img.width / img.height
                if aspect_ratio < 0.2 or aspect_ratio > 5.0:  # Proporciones razonables
                    return False
                    
                return True
        except Exception:
            return False

    def find_duplicate_images(self, directory):
        """Encontrar imágenes duplicadas usando hash perceptual"""
        images = {}
        for ext in self.extensions:
            for img_path in Path(directory).rglob(f'*{ext}'):
                try:
                    # Verificar tamaño de archivo
                    file_size = img_path.stat().st_size
                    if file_size < self.min_file_size or file_size > self.max_file_size:
                        continue
                        
                    # Verificar si es una imagen válida
                    if not self.is_valid_image(img_path):
                        continue
                        
                    # Calcular hash perceptual
                    with Image.open(img_path) as img:
                        # Redimensionar para mejorar el rendimiento
                        img_hash = str(imagehash.average_hash(img))
                        
                        if img_hash in images:
                            images[img_hash].append(img_path)
                        else:
                            images[img_hash] = [img_path]
                            
                except Exception as e:
                    logger.warning(f"No se pudo procesar {img_path}: {str(e)}")
        
        # Filtrar solo los hashes con duplicados
        return {k: v for k, v in images.items() if len(v) > 1}

    def clean_directory(self, directory, max_age_days=30):
        """Limpiar directorio de imágenes no utilizadas"""
        logger.info(f"Escaneando directorio: {directory}")
        
        if not Path(directory).exists():
            logger.error(f"El directorio no existe: {directory}")
            return
            
        deleted = 0
        skipped = 0
        errors = 0
        total_size = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Primero buscar duplicados
        logger.info("Buscando imágenes duplicadas...")
        duplicates = self.find_duplicate_images(directory)
        
        # Procesar duplicados
        for img_hash, img_paths in duplicates.items():
            # Mantener la más reciente, eliminar las demás
            img_paths.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for img_path in img_paths[1:]:  # Todas menos la más reciente
                if not self.is_image_used(img_path):
                    try:
                        file_size = img_path.stat().st_size
                        
                        if not self.dry_run:
                            img_path.unlink()
                            
                        logger.info(f"Eliminada imagen duplicada: {img_path} (hash: {img_hash[:8]}...)")
                        deleted += 1
                        total_size += file_size
                    except Exception as e:
                        logger.error(f"Error al eliminar {img_path}: {str(e)}")
                        errors += 1
                else:
                    logger.debug(f"Imagen duplicada encontrada: {img_path}")