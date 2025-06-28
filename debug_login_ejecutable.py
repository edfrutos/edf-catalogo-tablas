#!/usr/bin/env python3
"""
Script para diagnosticar problemas de login en el ejecutable
"""
import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_login_ejecutable.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Prueba la conexión a MongoDB"""
    try:
        logger.info("Probando conexión a MongoDB...")
        
        # Importar configuración embebida
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        from config_embedded import EmbeddedConfig
        
        logger.info(f"MongoDB URI: {EmbeddedConfig.MONGO_URI[:50]}...")
        
        # Probar conexión
        from pymongo import MongoClient
        client = MongoClient(EmbeddedConfig.MONGO_URI)
        
        # Probar acceso a la base de datos
        db = client[EmbeddedConfig.MONGODB_DB]
        collections = db.list_collection_names()
        logger.info(f"Conexión exitosa. Colecciones encontradas: {collections}")
        
        # Probar acceso a usuarios
        users_collection = db.users
        user_count = users_collection.count_documents({})
        logger.info(f"Usuarios en la base de datos: {user_count}")
        
        # Buscar usuario específico
        user = users_collection.find_one({"username": "edefrutos"})
        if user:
            logger.info(f"Usuario encontrado: {user.get('username')} - {user.get('email')} - Rol: {user.get('role')}")
            return True
        else:
            logger.error("Usuario 'edefrutos' no encontrado")
            return False
            
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {str(e)}")
        return False

def test_flask_app():
    """Prueba la aplicación Flask"""
    try:
        logger.info("Probando aplicación Flask...")
        
        # Importar la aplicación
        sys.path.append(os.path.dirname(__file__))
        from main_app import app
        
        with app.test_client() as client:
            # Probar ruta principal
            response = client.get('/')
            logger.info(f"Respuesta de /: Status {response.status_code}")
            
            # Probar ruta de login
            response = client.get('/auth/login')
            logger.info(f"Respuesta de /auth/login: Status {response.status_code}")
            
            # Probar login POST
            login_data = {
                'username': 'edefrutos',
                'password': '123456'
            }
            response = client.post('/auth/login', data=login_data, follow_redirects=True)
            logger.info(f"Respuesta de login POST: Status {response.status_code}")
            logger.info(f"Contenido de respuesta: {response.data[:200]}...")
            
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error probando Flask: {str(e)}")
        return False

def check_dependencies():
    """Verifica las dependencias necesarias"""
    try:
        logger.info("Verificando dependencias...")
        
        dependencies = [
            'flask',
            'flask_login',
            'pymongo',
            'werkzeug',
            'webview'
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                logger.info(f"✅ {dep} - OK")
            except ImportError as e:
                logger.error(f"❌ {dep} - ERROR: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error verificando dependencias: {str(e)}")

def main():
    """Función principal"""
    logger.info("=== DIAGNÓSTICO DE LOGIN EJECUTABLE ===")
    logger.info(f"Fecha: {datetime.now()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Directorio actual: {os.getcwd()}")
    
    # Verificar dependencias
    check_dependencies()
    
    # Probar MongoDB
    mongodb_ok = test_mongodb_connection()
    
    # Probar Flask
    flask_ok = test_flask_app()
    
    logger.info("=== RESUMEN ===")
    logger.info(f"MongoDB: {'✅ OK' if mongodb_ok else '❌ ERROR'}")
    logger.info(f"Flask: {'✅ OK' if flask_ok else '❌ ERROR'}")
    
    if mongodb_ok and flask_ok:
        logger.info("🎉 Diagnóstico completado - Todo parece estar funcionando")
    else:
        logger.error("⚠️ Se encontraron problemas que necesitan ser corregidos")

if __name__ == "__main__":
    main()
