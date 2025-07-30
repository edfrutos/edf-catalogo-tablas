# Script: __init__.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 __init__.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Admin routes module initialization.
"""
from .admin_main import admin_bp
from .admin_users import admin_users_bp
from .admin_system import admin_system_bp
from .admin_backups import admin_backups_bp
from .admin_database import admin_database_bp

__all__ = ['admin_bp', 'admin_users_bp', 'admin_system_bp', 'admin_backups_bp', 'admin_database_bp']