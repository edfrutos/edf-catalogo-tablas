# Script: admin_main.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_main.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Main admin routes and core functionality.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.routes.maintenance_routes import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/tools")
@admin_required
def tools_dashboard():
    """
    Dashboard de herramientas y scripts del sistema.
    Requiere login de administrador.
    """
    return render_template('admin/tools_dashboard.html')

# @admin_bp.route("/scripts-tools")
# def scripts_tools_overview():
#     """
#     Overview of available scripts and tools.
#     Requires admin login.
#     """
#     # Esta ruta está comentada para evitar conflictos con scripts_bp
#     # La funcionalidad de scripts y herramientas ahora está en /admin/tools/
#     pass