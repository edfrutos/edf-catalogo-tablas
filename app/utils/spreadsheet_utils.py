# Script: spreadsheet_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 spreadsheet_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import logging
from flask import current_app
from pymongo.collection import Collection
from typing import Optional, Dict, List, Any, Union
from bson.objectid import ObjectId
from app.utils.db_utils import get_db

logger = logging.getLogger(__name__)

def get_spreadsheet_collection() -> Optional[Collection]:
    """
    Obtiene la colección de spreadsheets desde la aplicación actual
    
    Returns:
        Collection: Colección de MongoDB para spreadsheets o None si no se puede obtener
    """
    try:
        # Intentar obtener la colección desde current_app
        spreadsheets_collection = getattr(current_app, 'spreadsheets_collection', None)
        
        # Si no está disponible directamente, intentar obtenerla desde la base de datos
        if spreadsheets_collection is None:
            spreadsheets_collection = get_db()['spreadsheets']
            
        return spreadsheets_collection
    except Exception as e:
        logger.error(f"Error al obtener la colección de spreadsheets: {str(e)}")
        return None

def get_spreadsheet_by_id(spreadsheet_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un spreadsheet por su ID
    
    Args:
        spreadsheet_id (str): ID del spreadsheet a buscar
        
    Returns:
        Dict: Documento del spreadsheet o None si no se encuentra
    """
    try:
        collection = get_spreadsheet_collection()
        if not collection:
            logger.error("No se pudo obtener la colección de spreadsheets")
            return None
            
        return collection.find_one({"_id": ObjectId(spreadsheet_id)})
    except Exception as e:
        logger.error(f"Error al obtener spreadsheet por ID: {str(e)}")
        return None

def get_spreadsheets_by_owner(owner: str) -> List[Dict[str, Any]]:
    """
    Obtiene todos los spreadsheets de un propietario específico
    
    Args:
        owner (str): Nombre de usuario o email del propietario
        
    Returns:
        List[Dict]: Lista de documentos de spreadsheets
    """
    try:
        collection = get_spreadsheet_collection()
        if not collection:
            logger.error("No se pudo obtener la colección de spreadsheets")
            return []
            
        return list(collection.find({"owner": owner}).sort("created_at", -1))
    except Exception as e:
        logger.error(f"Error al obtener spreadsheets por propietario: {str(e)}")
        return []

def save_spreadsheet(data: Dict[str, Any]) -> Optional[str]:
    """
    Guarda un nuevo spreadsheet en la base de datos
    
    Args:
        data (Dict): Datos del spreadsheet a guardar
        
    Returns:
        str: ID del spreadsheet guardado o None si hay error
    """
    try:
        collection = get_spreadsheet_collection()
        if not collection:
            logger.error("No se pudo obtener la colección de spreadsheets")
            return None
            
        result = collection.insert_one(data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error al guardar spreadsheet: {str(e)}")
        return None

def update_spreadsheet(spreadsheet_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Actualiza un spreadsheet existente
    
    Args:
        spreadsheet_id (str): ID del spreadsheet a actualizar
        update_data (Dict): Datos a actualizar
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        collection = get_spreadsheet_collection()
        if not collection:
            logger.error("No se pudo obtener la colección de spreadsheets")
            return False
            
        result = collection.update_one(
            {"_id": ObjectId(spreadsheet_id)},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error al actualizar spreadsheet: {str(e)}")
        return False

def delete_spreadsheet(spreadsheet_id: str) -> bool:
    """
    Elimina un spreadsheet de la base de datos
    
    Args:
        spreadsheet_id (str): ID del spreadsheet a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        collection = get_spreadsheet_collection()
        if not collection:
            logger.error("No se pudo obtener la colección de spreadsheets")
            return False
            
        result = collection.delete_one({"_id": ObjectId(spreadsheet_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error al eliminar spreadsheet: {str(e)}")
        return False
