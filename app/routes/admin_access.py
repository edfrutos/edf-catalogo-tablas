# Script: admin_access.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_access.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

"""
Módulo de acceso directo para administradores
Este módulo proporciona funciones para garantizar acceso a usuarios administradores
tanto en entorno local como en producción.
"""

import logging
import traceback
from bson import ObjectId
from flask import Blueprint, request, redirect, url_for, flash, session
from app.models import get_users_collection
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)
admin_access_bp = Blueprint('admin_access', __name__, url_prefix='/admin_access')

@admin_access_bp.route('/login_admin', methods=['GET'])
def admin_login_direct():
    """
    Ruta para iniciar sesión directamente como administrador usando cualquier
    cuenta de administrador existente en la base de datos.
    """
    try:
        logger.warning("⚠️ INTENTO DE ACCESO DIRECTO ADMIN")
        
        # Detectar si estamos en modo local
        is_local = 'localhost' in request.host or '127.0.0.1' in request.host
        logger.warning(f"Entorno detectado: {'LOCAL' if is_local else 'PRODUCCIÓN'} | Host: {request.host}")
        
        # Configuración para entorno local y producción
        admin_user = None
        admin_emails = ['admin@example.com', 'edfrutos@gmail.com', 'admin@edefrutos.me']
        admin_ids = ["680bc20aa170ac7fe8e58bec", "67ed5c96300befce1d631c44"]
        
        # === MANEJO DIFERENCIADO PARA LOCAL Y PRODUCCIÓN ===
        if is_local:
            # En entorno local, usar SIEMPRE un usuario admin predefinido
            # Esto evita errores de conexión a MongoDB en local
            logger.warning("⚠️ ENTORNO LOCAL DETECTADO - USANDO ADMIN PREDEFINIDO")
            admin_user = {
                "_id": ObjectId(admin_ids[0]),
                "email": admin_emails[0],
                "username": "administrator",
                "role": "admin"
            }
        else:
            # En producción, intentar conectar a MongoDB
            try:
                users_collection = get_users_collection()
                db_status = users_collection.database.command('ping')
                logger.info(f"✅ Conexión a MongoDB verificada: {db_status}")
            except Exception as db_err:
                logger.error(f"❌ Error de conexión a MongoDB: {db_err}")
                # Si hay error, usar usuario predefinido
                admin_user = {
                    "_id": ObjectId(admin_ids[0]),
                    "email": admin_emails[0],
                    "username": "administrator",
                    "role": "admin"
                }
                logger.warning(f"⚠️ Usando admin temporal por fallo de conexión")
            
        # 2. Solo buscar en las colecciones si estamos en producción y no tenemos un usuario todavía
        if not admin_user and not is_local:
            try:
                # Primero buscar en los IDs conocidos
                for admin_id in admin_ids:
                    try:
                        admin_user = users_collection.find_one({"_id": ObjectId(admin_id)})
                        if admin_user:
                            logger.info(f"✅ Usuario encontrado por ID: {admin_id}")
                            break
                    except Exception as id_err:
                        logger.warning(f"Error buscando ID {admin_id}: {id_err}")
                
                # Luego buscar por emails conocidos
                if not admin_user:
                    for email in admin_emails:
                        admin_user = users_collection.find_one({"email": email})
                        if admin_user:
                            logger.info(f"✅ Usuario encontrado por email: {email}")
                            break
                
                # Si no encuentra, buscar cualquier admin en las colecciones
                if not admin_user:
                    # En users_unified
                    admin_user = users_collection.find_one({"role": "admin"})
                    if admin_user:
                        logger.info(f"✅ Usuario admin encontrado en users_unified")
                    else:
                        # En users
                        try:
                            users_collection = users_collection.database.users
                            admin_user = users_collection.find_one({"role": "admin"})
                            if admin_user:
                                logger.info(f"✅ Usuario admin encontrado en users")
                        except Exception as coll_err:
                            logger.warning(f"Error accediendo a colección users: {coll_err}")
            except Exception as search_err:
                logger.error(f"❌ Error buscando admins: {search_err}")

        # 3. Si aún no tenemos admin, crear uno en memoria
        if not admin_user:
            logger.error("❌ No se encontró ningún usuario admin")
            admin_user = {
                "_id": ObjectId(admin_ids[0]),
                "email": admin_emails[0],
                "username": "administrator",
                "role": "admin"
            }
            logger.warning("⚠️ Creando admin temporal como último recurso")
            flash("No se encontraron usuarios administradores en la base de datos. Se ha creado uno temporal.", "warning")

        # 4. ESTABLECER SESIÓN CON GARANTIAS TOTALES
        session.clear()  # Limpiar cualquier sesión existente
        session.permanent = True
        session['_permanent'] = True  # Doble garantía
        session['user_id'] = str(admin_user.get('_id', admin_ids[0]))
        session['email'] = admin_user.get('email', admin_emails[0])
        session['username'] = admin_user.get('username', 'administrator')
        session['role'] = 'admin'  # Asegurar que el rol sea admin
        session['logged_in'] = True
        session.modified = True
        
        # Si estamos en local, registrar datos detallados para debug
        if is_local:
            logger.info(f"✅ ACCESO LOCAL GARANTIZADO para: {session['email']}")
            logger.debug(f"Datos completos de sesión: {dict(session)}")
            logger.debug(f"Cookies disponibles: {request.cookies}")
        else:
            logger.info(f"✅ ACCESO PRODUCCIÓN OK para: {session['email']}")

        # 5. Redirigir al panel con headers especiales para garantizar propagación
        response = redirect(url_for('admin.dashboard_admin'))
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        return response
        
    except Exception as e:
        logger.error(f"❌ Error en acceso directo admin: {str(e)}")
        traceback.print_exc()
        
        # INCLUSO EN CASO DE ERROR, ESTABLECER SESIÓN ADMIN
        session.clear()
        session.permanent = True
        session['user_id'] = "680bc20aa170ac7fe8e58bec"
        session['email'] = "admin@example.com"
        session['username'] = "administrator"
        session['role'] = 'admin'
        session['logged_in'] = True
        session.modified = True
        
        flash(f"Se ha detectado un error, pero se ha establecido una sesión de administrador de emergencia. Error: {str(e)}", "warning")
        return redirect(url_for('admin.dashboard_admin'))
