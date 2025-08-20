# Script: audit.py
# Descripción: [Módulo de auditoría para el registro de acciones de usuarios y sistema. Proporciona funciones para registrar eventos y consultar el historial de auditoría.]
# Uso: python3 audit.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Módulo de auditoría para el registro de acciones de usuarios y sistema.
Proporciona funciones para registrar eventos y consultar el historial de auditoría.
"""

import datetime
import logging
from typing import Any, Dict, Optional

from bson.objectid import ObjectId

from app.database import get_audit_logs_collection


def audit_log(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None, success: bool = True) -> bool:
    """
    Registra un evento de auditoría en la base de datos.

    Args:
        event_type (str): Tipo de evento (login, cambio_contraseña, acción_admin, etc.)
        user_id (str, optional): ID del usuario relacionado con el evento
        details (dict, optional): Detalles adicionales del evento
        ip_address (str, optional): Dirección IP desde donde se realizó la acción
        success (bool): Indica si la acción fue exitosa o falló

    Returns:
        bool: True si se registró correctamente, False en caso contrario
    """
    return log_event(event_type, user_id, details, ip_address, success)


def log_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None, success: bool = True) -> bool:
    """
    Registra un evento de auditoría en la base de datos.

    Args:
        event_type (str): Tipo de evento (login, cambio_contraseña, acción_admin, etc.)
        user_id (str, optional): ID del usuario relacionado con el evento
        details (dict, optional): Detalles adicionales del evento
        ip_address (str, optional): Dirección IP desde donde se realizó la acción
        success (bool): Indica si la acción fue exitosa o falló

    Returns:
        bool: True si se registró correctamente, False en caso contrario
    """
    try:
        audit_collection = get_audit_logs_collection()
        if audit_collection is None:
            logging.error("No se pudo obtener la colección de logs de auditoría")
            return False

        event = {
            "event_type": event_type,
            "timestamp": datetime.datetime.utcnow(),
            "success": success,
            "ip_address": ip_address,
        }

        if user_id:
            try:
                event["user_id"] = ObjectId(user_id)
            except Exception:
                event["user_id"] = user_id

        if details:
            event["details"] = details

        result = audit_collection.insert_one(event)
        return result.acknowledged
    except Exception as e:
        logging.error(f"Error al registrar evento de auditoría: {str(e)}")
        return False


def get_audit_logs(filters=None, limit=100, skip=0, sort_by="timestamp", sort_dir=-1):
    """
    Obtiene logs de auditoría con filtros opcionales.

    Args:
        filters (dict, optional): Filtros para la búsqueda
        limit (int, optional): Número máximo de registros a devolver
        skip (int, optional): Número de registros a omitir (para paginación)
        sort_by (str, optional): Campo por el cual ordenar
        sort_dir (int, optional): Dirección de ordenamiento (1=ascendente, -1=descendente)

    Returns:
        list: Lista de logs de auditoría encontrados
    """
    try:
        audit_collection = get_audit_logs_collection()
        if audit_collection is None:
            logging.error("No se pudo obtener la colección de logs de auditoría")
            return []

        query = filters or {}

        # Si hay un filtro por user_id, convertirlo a ObjectId
        if "user_id" in query and isinstance(query["user_id"], str):
            try:
                query["user_id"] = ObjectId(query["user_id"])
            except Exception:
                pass

        cursor = audit_collection.find(query)

        # Aplicar ordenamiento
        cursor = cursor.sort(sort_by, sort_dir)

        # Aplicar paginación
        cursor = cursor.skip(skip).limit(limit)

        return list(cursor)
    except Exception as e:
        logging.error(f"Error al obtener logs de auditoría: {str(e)}")
        return []


def count_audit_logs(filters=None):
    """
    Cuenta el número de logs de auditoría que coinciden con los filtros.

    Args:
        filters (dict, optional): Filtros para la búsqueda

    Returns:
        int: Número de logs encontrados
    """
    try:
        audit_collection = get_audit_logs_collection()
        if audit_collection is None:
            logging.error("No se pudo obtener la colección de logs de auditoría")
            return 0

        query = filters or {}

        # Si hay un filtro por user_id, convertirlo a ObjectId
        if "user_id" in query and isinstance(query["user_id"], str):
            try:
                query["user_id"] = ObjectId(query["user_id"])
            except Exception:
                pass

        return audit_collection.count_documents(query)
    except Exception as e:
        logging.error(f"Error al contar logs de auditoría: {str(e)}")
        return 0
