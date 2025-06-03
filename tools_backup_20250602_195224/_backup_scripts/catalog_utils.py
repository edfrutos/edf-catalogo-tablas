#!/usr/bin/env python3
from pymongo import MongoClient
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import openpyxl
from bson import ObjectId

class CatalogUtils:
    def __init__(self, db):
        self.db = db
        self.catalogos_collection = db['catalogos']
        self.spreadsheets_collection = db['67b8c24a7fdc72dd4d8703cf']
        self.SPREADSHEET_FOLDER = "/spreadsheets"
        
        # Asegurar que el directorio existe
        if not os.path.exists(self.SPREADSHEET_FOLDER):
            os.makedirs(self.SPREADSHEET_FOLDER, exist_ok=True)

    def crear_catalogo(self, nombre, descripcion, propietario):
        """Crea un nuevo catálogo manualmente"""
        try:
            # Validar que el propietario exista
            user = self.db['users'].find_one({'email': propietario})
            if not user:
                return False, "El propietario especificado no existe"
            
            # Crear nuevo catálogo
            catalogo = {
                'nombre': nombre,
                'descripcion': descripcion,
                'propietario': propietario,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'estado': 'activo',
                'tablas': []
            }
            
            result = self.catalogos_collection.insert_one(catalogo)
            return True, str(result.inserted_id)
            
        except Exception as e:
            return False, f"Error al crear el catálogo: {str(e)}"

    def importar_catalogo(self, archivo, nombre, propietario):
        """Importa una tabla para crear un nuevo catálogo"""
        try:
            # Validar que el propietario exista
            user = self.db['users'].find_one({'email': propietario})
            if not user:
                return False, "El propietario especificado no existe"
            
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"{os.path.splitext(archivo.filename)[0]}_{timestamp}{os.path.splitext(archivo.filename)[1]}"
            ruta_archivo = os.path.join(self.SPREADSHEET_FOLDER, nombre_archivo)
            
            # Guardar el archivo
            archivo.save(ruta_archivo)
            
            # Crear nuevo catálogo
            catalogo = {
                'nombre': nombre,
                'descripcion': f'Importado desde {archivo.filename}',
                'propietario': propietario,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'estado': 'activo',
                'tablas': [{
                    'nombre': nombre_archivo,
                    'archivo': nombre_archivo,
                    'ultima_modificacion': datetime.now()
                }]
            }
            
            result = self.catalogos_collection.insert_one(catalogo)
            return True, str(result.inserted_id)
            
        except Exception as e:
            # Eliminar archivo si hay error
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
            return False, f"Error al importar el catálogo: {str(e)}"

    def listar_catalogos(self):
        """Lista todos los catálogos con sus detalles"""
        try:
            catalogos = list(self.catalogos_collection.find())
            return True, catalogos
        except Exception as e:
            return False, f"Error al listar catálogos: {str(e)}"
