#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de limpieza periódica de imágenes no utilizadas

Este script:
1. Se conecta a MongoDB
2. Verifica qué imágenes locales en 'imagenes_subidas' no están siendo referenciadas
3. Mueve las imágenes no utilizadas a 'unused_images' o las elimina según configuración
4. Registra toda la operación en un archivo de log específico
5. Envía un correo con el resumen si se configuró para ello
"""

import os
import sys
import shutil
import logging
import smtplib
import datetime
import certifi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Forzar el uso del bundle de certificados de certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Configuración del script
class Config:
    # Directorio raíz del proyecto (ajustar si es necesario)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Directorio de imágenes subidas
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "imagenes_subidas")
    
    # Directorio para imágenes no utilizadas
    UNUSED_IMAGES_FOLDER = os.path.join(BASE_DIR, "unused_images")
    
    # Archivo de log específico para este script
    LOG_FILE = os.path.join(BASE_DIR, "logs", "clean_images.log")
    
    # Configuración de MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "app_catalogojoyero_nueva")
    
    # Modo: 'move' para mover archivos, 'delete' para eliminarlos directamente
    CLEANUP_MODE = os.getenv("CLEANUP_MODE", "move")
    
    # Configuración de correo
    SEND_EMAIL = os.getenv("SEND_EMAIL", "False").lower() == "true"
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    EMAIL_SERVER = os.getenv("EMAIL_SERVER", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Configuración de logging
def setup_logging():
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(Config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar el logger
    logger = logging.getLogger('clean_images')
    logger.setLevel(logging.INFO)
    
    # Handler para archivo
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato para los logs
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Conexión a MongoDB
def connect_to_mongodb():
    try:
        # Configurar opciones de conexión segura para MongoDB Atlas
        client = MongoClient(
            Config.MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1'),
            retryWrites=True,
            w='majority'
        )
        db = client[Config.MONGO_DB]
        logger.info(f"Conexión exitosa a MongoDB: {Config.MONGO_URI}")
        logger.info(f"Base de datos: {Config.MONGO_DB}")
        
        # Obtener las colecciones disponibles
        collections = db.list_collection_names()
        logger.info(f"Colecciones disponibles: {collections}")
        
        return db
    except Exception as e:
        logger.error(f"Error al conectar a MongoDB: {str(e)}")
        sys.exit(1)

# Obtener todas las imágenes referenciadas en MongoDB
def get_referenced_images(db):
    referenced_images = set()
    total_documents = 0
    documents_with_images = 0
    
    logger.info("Buscando imágenes referenciadas en la base de datos...")
    
    # Colección principal de catálogo (específica para esta aplicación)
    catalog_collection_name = '67b8c24a7fdc72dd4d8703cf'
    
    # Iterar por todas las colecciones, pero priorizar la colección de catálogo
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        
        # Información adicional para la colección de catálogo
        if collection_name == catalog_collection_name:
            logger.info(f"Procesando colección principal de catálogo: {collection_name}")
        
        # Contar documentos en la colección
        collection_count = collection.count_documents({})
        total_documents += collection_count
        
        # Buscar documentos con imágenes
        # Buscar documentos con imágenes
        for doc in collection.find({}, {"Imagenes": 1}):
            if "Imagenes" in doc and doc["Imagenes"]:
                documents_with_images += 1
                
                if collection_name == catalog_collection_name:
                    logger.debug(f"Encontrado documento con imágenes en catálogo: {doc['_id']}")
                # Procesar cada imagen
                for img_path in doc["Imagenes"]:
                    # Ignorar valores None o imágenes en S3
                    if img_path is None:
                        continue
                    if img_path.startswith("s3://"):
                        continue
                    
                    # Extraer solo el nombre del archivo
                    if "/" in img_path:
                        img_name = img_path.split("/")[-1]
                    else:
                        img_name = img_path
                    
                    referenced_images.add(img_name)
    
    logger.info(f"Total de documentos analizados: {total_documents}")
    logger.info(f"Documentos con imágenes: {documents_with_images}")
    logger.info(f"Imágenes locales referenciadas: {len(referenced_images)}")
    
    return referenced_images

# Obtener todas las imágenes existentes en el directorio local
def get_local_images():
    local_images = set()
    
    # Verificar que el directorio de imágenes exista
    if not os.path.exists(Config.UPLOAD_FOLDER):
        logger.warning(f"El directorio {Config.UPLOAD_FOLDER} no existe. Creándolo...")
        os.makedirs(Config.UPLOAD_FOLDER)
        return local_images
    
    # Listar todos los archivos en el directorio
    for filename in os.listdir(Config.UPLOAD_FOLDER):
        if os.path.isfile(os.path.join(Config.UPLOAD_FOLDER, filename)):
            local_images.add(filename)
    
    logger.info(f"Total de archivos encontrados en {Config.UPLOAD_FOLDER}: {len(local_images)}")
    return local_images

# Limpiar imágenes no utilizadas
def clean_unused_images(referenced_images, local_images):
    if not local_images:
        logger.info("No hay imágenes locales para procesar.")
        return {"moved": 0, "deleted": 0, "errors": 0, "details": []}
    
    # Preparar directorio para imágenes no utilizadas si el modo es 'move'
    if Config.CLEANUP_MODE == "move" and not os.path.exists(Config.UNUSED_IMAGES_FOLDER):
        os.makedirs(Config.UNUSED_IMAGES_FOLDER)
        logger.info(f"Directorio creado: {Config.UNUSED_IMAGES_FOLDER}")
    
    # Identificar imágenes no utilizadas
    unused_images = local_images - referenced_images
    logger.info(f"Imágenes no utilizadas: {len(unused_images)}")
    
    # Verificación adicional para estadísticas
    unused_count = max(0, len(local_images) - len(referenced_images))
    
    # Estadísticas
    stats = {
        "moved": 0,
        "deleted": 0,
        "errors": 0,
        "details": []
    }
    
    # Procesar cada imagen no utilizada
    for img_name in unused_images:
        src_path = os.path.join(Config.UPLOAD_FOLDER, img_name)
        
        try:
            # Modo 'move': mover a directorio de imágenes no utilizadas
            if Config.CLEANUP_MODE == "move":
                dst_path = os.path.join(Config.UNUSED_IMAGES_FOLDER, img_name)
                shutil.move(src_path, dst_path)
                logger.info(f"Imagen movida: {img_name}")
                stats["moved"] += 1
                stats["details"].append(f"Movida: {img_name}")
            
            # Modo 'delete': eliminar directamente
            elif Config.CLEANUP_MODE == "delete":
                os.remove(src_path)
                logger.info(f"Imagen eliminada: {img_name}")
                stats["deleted"] += 1
                stats["details"].append(f"Eliminada: {img_name}")
        
        except Exception as e:
            error_msg = f"Error al procesar {img_name}: {str(e)}"
            logger.error(error_msg)
            stats["errors"] += 1
            stats["details"].append(error_msg)
    
    return stats

# Enviar correo con el resumen
def send_email_summary(stats, referenced_images, local_images):
    if not Config.SEND_EMAIL:
        logger.info("Envío de correo desactivado.")
        return
    
    if not all([Config.EMAIL_FROM, Config.EMAIL_TO, Config.EMAIL_SERVER, 
                Config.EMAIL_USER, Config.EMAIL_PASSWORD]):
        logger.warning("Faltan datos para enviar el correo. Verificar configuración.")
        return
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = Config.EMAIL_FROM
        msg['To'] = Config.EMAIL_TO
        msg['Subject'] = f"Reporte de limpieza de imágenes - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Preparar contenido
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #2c3e50; }}
                .stats {{ margin-bottom: 20px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h2>Reporte de limpieza de imágenes</h2>
            
            <div class="stats">
                <p><strong>Imágenes referenciadas:</strong> {len(referenced_images)}</p>
                <p><strong>Imágenes locales encontradas:</strong> {len(local_images)}</p>
                <p><strong>Imágenes no utilizadas:</strong> {len(local_images) - len(referenced_images)}</p>
            </div>
            
            <div class="stats">
                <p><strong>Modo de limpieza:</strong> {Config.CLEANUP_MODE}</p>
                <p class="success"><strong>Imágenes movidas:</strong> {stats['moved']}</p>
                <p class="warning"><strong>Imágenes eliminadas:</strong> {stats['deleted']}</p>
                <p class="error"><strong>Errores:</strong> {stats['errors']}</p>
            </div>
            
            <h3>Detalles:</h3>
            <ul>
        """
        
        # Añadir detalles (limitar a 20 elementos para evitar correos muy grandes)
        for detail in stats['details'][:20]:
            body += f"<li>{detail}</li>\n"
        
        if len(stats['details']) > 20:
            body += f"<li>... y {len(stats['details']) - 20} más (ver archivo de log para detalles completos)</li>\n"
        
        body += """
            </ul>
            <p>Para más detalles, consultar el archivo de log.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Conectar al servidor y enviar
        server = smtplib.SMTP(Config.EMAIL_SERVER, Config.EMAIL_PORT)
        server.starttls()
        server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Correo enviado exitosamente a {Config.EMAIL_TO}")
    
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")

# Función principal
def main():
    logger.info("=== Iniciando proceso de limpieza de imágenes ===")
    
    # Conectar a MongoDB
    db = connect_to_mongodb()
    
    # Obtener imágenes referenciadas
    referenced_images = get_referenced_images(db)
    
    # Obtener imágenes locales
    local_images = get_local_images()
    
    # Limpiar imágenes no utilizadas
    stats = clean_unused_images(referenced_images, local_images)
    
    # Resumen final
    logger.info("=== Resumen de la operación ===")
    logger.info(f"Imágenes referenciadas: {len(referenced_images)}")
    logger.info(f"Imágenes locales: {len(local_images)}")
    logger.info(f"Imágenes no utilizadas: {max(0, len(local_images) - len(referenced_images))}")
    logger.info(f"Imágenes movidas: {stats['moved']}")
    logger.info(f"Imágenes eliminadas: {stats['deleted']}")
    logger.info(f"Errores: {stats['errors']}")
    
    # Enviar correo con el resumen
    send_email_summary(stats, referenced_images, local_images)
    
    logger.info("=== Proceso de limpieza finalizado ===")

if __name__ == "__main__":
    # Configurar logging
    logger = setup_logging()
    
    try:
        main()
    except Exception as e:
        logger.error(f"Error general en la ejecución: {str(e)}", exc_info=True)
        sys.exit(1)

