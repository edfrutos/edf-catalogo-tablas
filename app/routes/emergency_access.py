# Script: emergency_access.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 emergency_access.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

"""
Rutas de acceso de emergencia que establecen la sesión directamente
sin depender del sistema normal de inicio de sesión.
"""

import os
import logging
from bson import ObjectId
from flask import Blueprint, render_template, redirect, url_for, session, flash
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/user_login_bypass')
def user_login_bypass():
    """Establece una sesión de usuario normal directamente sin validación"""
    try:
        session.clear()
        session.permanent = True
        # Unificar criterios: establecer username, email y user_id
        session['user_id'] = '680d462bcccecbe06cc93ea4'
        session['email'] = 'usuario@example.com'
        session['username'] = 'usuario_normal'
        session['role'] = 'user'
        session['logged_in'] = True
        session.modified = True
        logger.warning(f"✅ ACCESO DIRECTO: Sesión establecida para usuario normal: {session['email']}")
        flash('Has iniciado sesión como usuario normal mediante acceso directo', 'success')
        return redirect('/')
    except Exception as e:
        logger.error(f"❌ Error en acceso directo: {str(e)}")
        flash(f"Error al establecer sesión: {str(e)}", "error")
        return redirect(url_for('auth.login'))

@emergency_bp.route('/admin_login_bypass') 
def admin_login_bypass():
    """Establece una sesión de administrador directamente sin validación"""
    try:
        session.clear()
        session.permanent = True
        # Unificar criterios: establecer username, email y user_id
        session['user_id'] = '680bc20aa170ac7fe8e58bec'
        session['email'] = 'admin@example.com'
        session['username'] = 'administrator'
        session['role'] = 'admin'
        session['logged_in'] = True
        session.modified = True
        logger.warning(f"✅ ACCESO DIRECTO: Sesión establecida para administrador: {session['email']}")
        flash('Has iniciado sesión como administrador mediante acceso directo', 'success')
        return redirect('/admin/')
    except Exception as e:
        logger.error(f"❌ Error en acceso directo admin: {str(e)}")
        flash(f"Error al establecer sesión: {str(e)}", "error")
        return redirect(url_for('auth.login'))
