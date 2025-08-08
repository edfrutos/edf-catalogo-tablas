#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from flask import url_for
from app import create_app
from app.database import get_users_collection, initialize_db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_profile_images():
    """Verifica las rutas de las imágenes de perfil de los usuarios."""
    
    app = create_app()
    
    with app.app_context():
        # Inicializar la conexión a la base de datos
        initialize_db(app)
        
        # Obtener la colección de usuarios
        users_collection = get_users_collection()
        
        if users_collection is None:
            logger.error("No se pudo conectar a la base de datos")
            return
        
        users = users_collection.find({})
        
        logger.info("Verificando rutas de imágenes de perfil...")
        
        for user in users:
            if 'foto_perfil' in user and user['foto_perfil']:
                # Construir la ruta completa del archivo
                image_path = os.path.join(app.static_folder, 'uploads', user['foto_perfil'])
                
                # Verificar si el archivo existe
                if os.path.exists(image_path):
                    logger.info(f"✅ Usuario {user.get('email')}: Imagen encontrada en {image_path}")
                else:
                    logger.error(f"❌ Usuario {user.get('email')}: Imagen no encontrada en {image_path}")
                    
                # Verificar la ruta en las plantillas
                with app.test_request_context():
                    template_path = url_for('static', filename=f'uploads/{user["foto_perfil"]}')
                    logger.info(f"   URL en plantilla: {template_path}")
            else:
                logger.info(f"ℹ️ Usuario {user.get('email')}: No tiene foto de perfil configurada")

if __name__ == "__main__":
    test_profile_images()
