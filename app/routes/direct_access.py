# Script: direct_access.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 direct_access.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Módulo para acceso directo al panel de administración
Proporciona una solución universal que funciona tanto en entorno
local como en producción, sin depender de la conexión a MongoDB.
"""

import os
import logging
from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app

logger = logging.getLogger(__name__)
direct_access_bp = Blueprint('direct_access', __name__)

@direct_access_bp.route('/local_admin')
def local_admin_page():
    """Página HTML estática para acceso directo de admin"""
    return render_template('local_admin_login.html')

@direct_access_bp.route('/local_user')
def local_user_page():
    """Página HTML estática para acceso directo de usuario normal"""
    return render_template('local_user_login.html')

@direct_access_bp.route('/set_admin_session', methods=['POST'])
def set_admin_session():
    """Establece la sesión de administrador directamente"""
    try:
        # Obtener datos del formulario
        admin_id = request.form.get('admin_id', '680bc20aa170ac7fe8e58bec')
        email = request.form.get('email', 'admin@example.com')
        username = request.form.get('username', 'administrator')
        
        # Verificar que sean valores válidos
        if not (admin_id and email and username):
            flash("Datos incompletos para establecer sesión", "error")
            return redirect(url_for('auth.login'))
        
        # Limpiar sesión anterior
        session.clear()
        
        # Establecer nueva sesión de administrador
        session.permanent = True
        session['_permanent'] = True
        session['user_id'] = admin_id
        session['email'] = email
        session['username'] = username
        session['role'] = 'admin'
        session['logged_in'] = True
        session.modified = True
        
        logger.warning(f"✅ ACCESO DIRECTO ADMIN ACTIVADO: {email}")
        
        # Redirigir al panel de administración
        response = redirect(url_for('admin.dashboard_admin'))
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        return response
        
    except Exception as e:
        logger.error(f"Error en acceso directo admin: {str(e)}")
        flash(f"Error al establecer sesión: {str(e)}", "error")
        return redirect(url_for('auth.login'))
        
@direct_access_bp.route('/set_user_session', methods=['POST'])
def set_user_session():
    """Establece la sesión de usuario normal directamente"""
    try:
        # Obtener datos del formulario
        user_id = request.form.get('user_id', '67ed5c96300befce1d631c45')
        email = request.form.get('email', 'usuario@example.com')
        username = request.form.get('username', 'usuario_normal')
        
        # Verificar que sean valores válidos
        if not (user_id and email and username):
            flash("Datos incompletos para establecer sesión", "error")
            return redirect(url_for('auth.login'))
        
        # Limpiar sesión anterior
        session.clear()
        
        # Establecer nueva sesión de usuario normal
        session.permanent = True
        session['_permanent'] = True
        session['user_id'] = user_id
        session['email'] = email
        session['username'] = username
        session['role'] = 'user'
        session['logged_in'] = True
        session.modified = True
        
        logger.warning(f"✅ ACCESO DIRECTO USUARIO ACTIVADO: {email}")
        
        # Redirigir al dashboard de usuario
        response = redirect(url_for('main.dashboard'))
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        return response
        
    except Exception as e:
        logger.error(f"Error en acceso directo usuario: {str(e)}")
        flash(f"Error al establecer sesión de usuario: {str(e)}", "error")
        return redirect(url_for('auth.login'))
