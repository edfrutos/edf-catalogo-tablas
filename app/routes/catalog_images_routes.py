# Script: catalog_images_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 catalog_images_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
from flask import Blueprint, request, redirect, url_for, flash, current_app, render_template, session
from werkzeug.utils import secure_filename
from app.extensions import mongo, is_mongo_available
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

image_bp = Blueprint('images', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@image_bp.route('/catalogs/<catalog_id>/upload-images', methods=['POST'])
def upload_images(catalog_id):
    try:
        if not is_mongo_available():
            flash('Error de conexión a la base de datos.', 'danger')
            return redirect(url_for('catalogs.view', catalog_id=catalog_id))
        
        # Buscar el catálogo en múltiples colecciones
        catalog = None
        collections_to_check = ['catalogs', 'spreadsheets']
        
        for collection_name in collections_to_check:
            collection = getattr(mongo.db, collection_name)
            catalog = collection.find_one({'_id': ObjectId(catalog_id)})
            if catalog:
                current_collection = collection
                break
        
        if not catalog:
            flash("Catálogo no encontrado.", "danger")
            return redirect(url_for('catalogs.view', catalog_id=catalog_id))

        files = request.files.getlist('images')
        if not files or all(not file.filename for file in files):
            flash("No se han seleccionado imágenes.", "warning")
            return redirect(url_for('catalogs.view', catalog_id=catalog_id))
            
        # Eliminar la restricción de 3 imágenes
        if len(files) > 10:  # Aumentar el límite a 10 imágenes por carga
            flash("Sólo puedes subir hasta 10 imágenes a la vez.", "warning")
            return redirect(url_for('catalogs.view', catalog_id=catalog_id))

        # Crear directorio de uploads si no existe
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Obtener imágenes existentes o inicializar lista vacía
        existing_images = catalog.get('images', [])
        if not isinstance(existing_images, list):
            existing_images = []
            
        image_names = existing_images.copy()
        
        for index, file in enumerate(files):
            if file and file.filename and allowed_file(file.filename):
                # Generar un nombre único para la imagen
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = secure_filename(file.filename)
                extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                image_name = f"{catalog_id}_{timestamp}_{index}.{extension}"
                
                # Guardar la imagen en el sistema de archivos
                save_path = os.path.join(upload_folder, image_name)
                file.save(save_path)
                
                # Añadir a la lista de imágenes
                image_names.append(image_name)
                
                current_app.logger.info(f"Imagen guardada: {save_path}")

        # Actualizar el catálogo con las nuevas imágenes en ambos campos para mantener compatibilidad
        try:
            # Actualizar tanto el campo 'images' como 'imagenes' para mantener compatibilidad
            current_collection.update_one(
                {'_id': ObjectId(catalog_id)},
                {'$set': {
                    'images': image_names,
                    'imagenes': image_names,
                    'updated_at': datetime.now()
                }}
            )
            
            logger.info(f"Catálogo {catalog_id} actualizado con {len(image_names)} imágenes")
        except Exception as e:
            logger.error(f"Error al actualizar imágenes en el catálogo: {str(e)}")
            raise e
        
        current_app.logger.info(f"Catálogo actualizado con imágenes: {image_names}")
        flash("Imágenes subidas correctamente.", "success")
        
    except Exception as e:
        current_app.logger.error(f"Error al subir imágenes: {str(e)}", exc_info=True)
        flash(f"Error al subir imágenes: {str(e)}", "danger")
    
    return redirect(url_for('catalogs.view', catalog_id=catalog_id))
