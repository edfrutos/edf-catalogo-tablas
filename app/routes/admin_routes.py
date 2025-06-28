# Script: admin_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from functools import wraps
import logging
import re
import subprocess
import time
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, jsonify, current_app, abort
from flask_login import current_user
from bson import ObjectId
from app.database import (get_reset_tokens_collection, get_users_collection,
                      get_audit_logs_collection, get_catalogs_collection, get_mongo_client, get_mongo_db, get_last_error)
from app.audit import audit_log
from app.routes.maintenance_routes import admin_required
import app.monitoring as monitoring
import app.notifications as notifications
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import io
import csv
import json
import os
import shutil
from flask import send_file
from app.extensions import is_mongo_available
from app.utils.db_utils import get_db
from tools.db_utils.google_drive_utils import upload_to_drive
from subprocess import Popen, PIPE
import certifi
import traceback
import pprint
import psutil
import platform

def log_action(action, message, details=None, user_id=None, collection=None):
    """
    Registra una acción en el log de auditoría.
    
    Args:
        action (str): Nombre de la acción (ej: 'backup_created', 'user_updated')
        message (str): Mensaje descriptivo de la acción
        details (dict, optional): Detalles adicionales de la acción
        user_id (str, optional): ID del usuario que realizó la acción
        collection (str, optional): Nombre de la colección relacionada
    """
    try:
        # Obtener el ID de usuario actual si no se proporciona
        if not user_id and hasattr(current_user, 'id'):
            user_id = str(current_user.id)
            
        # Crear el documento de log
        log_entry = {
            'action': action,
            'message': message,
            'details': details or {},
            'user_id': user_id,
            'collection': collection,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'timestamp': datetime.utcnow()
        }
        
        # Insertar en la colección de auditoría
        audit_logs = get_audit_logs_collection()
        audit_logs.insert_one(log_entry)
        
        # También registrar en el log de la aplicación
        current_app.logger.info(f"[AUDIT] {action}: {message}")
        
    except Exception as e:
        current_app.logger.error(f"Error al registrar en el log de auditoría: {str(e)}", exc_info=True)

# Importar nuestro módulo de monitoreo
from app import monitoring

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")



@admin_bp.route('/scripts-tools')
def scripts_tools_overview():
    import os
    # Verificar si el usuario está logueado y es admin usando session
    if 'user_id' not in session or not session.get('logged_in', False):
        flash('Debes iniciar sesión para acceder.', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    # Verificar si el usuario tiene rol de admin
    if session.get('role') != 'admin':
        flash('No tienes permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    def list_dir_names(path):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
        full = os.path.join(base, path)
        if not os.path.isdir(full):
            return []
        items = []
        for name in sorted(os.listdir(full)):
            if name.startswith('.'):
                continue
            items.append(name + ('/' if os.path.isdir(os.path.join(full, name)) else ''))
        return items
    scripts_list = list_dir_names('scripts')
    tests_list = list_dir_names('tests')
    tools_list = list_dir_names('tools')
    return render_template('admin/scripts_tools_overview.html', scripts_list=scripts_list, tests_list=tests_list, tools_list=tools_list)


@admin_bp.route("/")
@admin_required
def dashboard_admin():
    # Mostrar advertencia si el sistema de monitoreo no está disponible
    if not getattr(current_app, "monitoring_enabled", False):
        flash("El sistema de monitoreo no está disponible actualmente. Contacte con el administrador.", "warning")
    db = get_db()
    if db is None:
        flash('No se pudo acceder a la base de datos. Contacte con el administrador.', 'error')
        return render_template("error.html", mensaje="No se pudo conectar a la base de datos. Contacte con el administrador.")
    users_collection = getattr(current_app, 'users_collection', None)
    if users_collection is None:
        flash('No se pudo acceder a la colección de usuarios.', 'error')
        return render_template("error.html", mensaje="No se pudo conectar a la colección de usuarios.")
    try:
        # Obtener parámetros de búsqueda
        search = request.args.get('search', '').strip()
        search_type = request.args.get('search_type', 'name')
        # Obtener todos los usuarios
        usuarios = list(users_collection.find())
        total_usuarios = len(usuarios)
        try:
            tablas = list(db['spreadsheets'].find().sort('created_at', -1))
        except Exception as e:
            print(f"[ERROR][ADMIN] Consulta a spreadsheets falló: {e}")
            tablas = []
        try:
            catalogos = list(db['catalogs'].find().sort('created_at', -1))

        except Exception as e:
            print(f"[ERROR][ADMIN] Consulta a catalogs falló: {e}")
            catalogos = []
        for t in tablas:
            t['tipo'] = 'spreadsheet'
            t['data'] = t.get('data', [])
        for c in catalogos:
            c['tipo'] = 'catalog'
            c['data'] = c.get('rows', [])
        registros = tablas + catalogos
        total_catalogos = len(registros)
        # Procesar usuarios con catálogos/tablas
        catalogos_por_usuario = {}
        for usuario in usuarios:
            catalogos_por_usuario[str(usuario['_id'])] = {
                'email': usuario.get('email', 'Sin email'),
                'nombre': usuario.get('name', usuario.get('username', 'Sin nombre')),
                'username': usuario.get('username', 'Sin usuario'),
                'role': usuario.get('role', 'user'),
                'count': 0,
                'last_update': None
            }
        for reg in registros:
            owner = reg.get('owner') or reg.get('created_by') or reg.get('owner_name')
            for user_id, user_info in catalogos_por_usuario.items():
                if user_info['username'] == owner or user_info['email'] == owner:
                    catalogos_por_usuario[user_id]['count'] += 1
                    if 'updated_at' in reg and reg['updated_at']:
                        last_update = reg['updated_at']
                        if isinstance(last_update, str):
                            try:
                                last_update = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                            except:
                                try:
                                    last_update = datetime.strptime(last_update, '%Y-%m-%d %H:%M')
                                except:
                                    last_update = None
                        if last_update and (catalogos_por_usuario[user_id]['last_update'] is None or last_update > catalogos_por_usuario[user_id]['last_update']):
                            catalogos_por_usuario[user_id]['last_update'] = last_update
        usuarios_con_catalogos = []
        for user_id, user_info in catalogos_por_usuario.items():
            if user_info['last_update']:
                user_info['last_update_str'] = user_info['last_update'].strftime('%d/%m/%Y, %H:%M:%S')
            else:
                user_info['last_update_str'] = 'No disponible'
            user_info['id'] = user_id
            usuarios_con_catalogos.append(user_info)
        usuarios_con_catalogos.sort(key=lambda x: x['count'], reverse=True)
        # FILTRO: aplicar búsqueda a registros y usuarios
        registros_filtrados = registros
        usuarios_filtrados = usuarios_con_catalogos
        if search:
            if search_type == 'name':
                registros_filtrados = [r for r in registros if search.lower() in (r.get('name','').lower())]
            elif search_type == 'owner':
                registros_filtrados = [r for r in registros if search.lower() in str(r.get('owner','')).lower() or search.lower() in str(r.get('created_by','')).lower() or search.lower() in str(r.get('owner_name','')).lower()]
            # Filtrar usuarios también
            if search_type == 'owner':
                usuarios_filtrados = [u for u in usuarios_con_catalogos if search.lower() in u['username'].lower() or search.lower() in u['email'].lower() or search.lower() in u['nombre'].lower()]
            elif search_type == 'name':
                # Mostrar todos los usuarios si se busca por nombre de catálogo
                usuarios_filtrados = usuarios_con_catalogos
        porcentaje = float(len(registros_filtrados)) / float(total_usuarios) * 100.0 if total_usuarios > 0 else 0.0
        # Filtrar catálogos/tablas propios del usuario logueado
        username = session.get('username')
        mis_registros = [r for r in registros if r.get('owner') == username or r.get('created_by') == username or r.get('owner_name') == username]
        response = make_response(render_template("admin/dashboard_admin.html",
                                                total_usuarios=total_usuarios,
                                                total_catalogos=len(registros_filtrados),
                                                registros=registros_filtrados,
                                                mis_registros=mis_registros,
                                                usuarios=usuarios_filtrados,
                                                porcentaje=porcentaje,
                                                tablas=[r for r in registros_filtrados if r['tipo']=='spreadsheet'],
                                                catalogos=[r for r in registros_filtrados if r['tipo']=='catalog'],
                                                search=search,
                                                search_type=search_type))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error en dashboard_admin: {str(e)}")
        return render_template("error.html", error=f"Error en el panel de administración: {str(e)}"), 500

# Removed duplicate maintenance route - using dedicated maintenance blueprint instead

@admin_bp.route("/system-status")
@admin_required
def system_status():
    import time
    t0 = time.time()
    try:
        print("[DEBUG][STATUS] Inicio carga system-status")
        # Obtener datos del sistema
        t1 = time.time()
        data = get_system_status_data()
        t2 = time.time()
        print(f"[DEBUG][STATUS] get_system_status_data: {t2-t1:.2f}s")
        # Obtener la lista de archivos de log
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
        t3 = time.time()
        log_files = get_log_files(logs_dir)
        t4 = time.time()
        print(f"[DEBUG][STATUS] get_log_files: {t4-t3:.2f}s")
        # Obtener la lista de archivos de backup
        backup_dir = os.path.abspath(os.path.join(os.getcwd(), 'backups'))
        t5 = time.time()
        backup_files = get_backup_files(backup_dir)
        t6 = time.time()
        print(f"[DEBUG][STATUS] get_backup_files: {t6-t5:.2f}s")
        print(f"[DEBUG][STATUS] TOTAL system-status: {time.time()-t0:.2f}s")
        # Pasar cache_stats y temp_files como variables independientes para el template
        cache_stats = data.get('cache_stats')
        temp_files = data.get('temp_files')
        return render_template('admin/system_status.html', data=data, log_files=log_files, backup_files=backup_files, cache_stats=cache_stats, temp_files=temp_files)
    except Exception as e:
        logger.error(f"Error en system_status: {str(e)}", exc_info=True)
        flash("Error al obtener el estado del sistema", "danger")
        return redirect(url_for('admin.dashboard_admin'))

@admin_bp.route("/system-status/report")
@admin_required
def system_status_report():
    import json
    data = get_system_status_data(full=True)
    response = current_app.response_class(
        response=json.dumps(data, indent=2, default=str),
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = 'attachment; filename=system_status_report.json'
    return response

from app.cache_system import get_cache_stats

from app.routes.temp_files_utils import list_temp_files, delete_temp_files

def get_system_status_data(full=False):
    import time
    t0 = time.time()
    try:
        # Obtener informe completo de estado (NO recalcular nada costoso aquí)
        t1 = time.time()
        health_report = monitoring.get_health_status()
        t2 = time.time()
        # Obtener estadísticas de solicitudes
        request_stats = monitoring._app_metrics["request_stats"]
        # Calcular uptime
        start_time = datetime.strptime(monitoring._app_metrics["start_time"], "%Y-%m-%d %H:%M:%S")
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split('.')[0]  # Formato HH:MM:SS
        # Obtener métricas de memoria
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        system_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        # Top 5 procesos por consumo de memoria
        all_procs = [p for p in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']) if p.info.get('memory_percent') is not None]
        top_procs = sorted(all_procs, key=lambda p: p.info['memory_percent'], reverse=True)[:5]
        top_processes = [
            {
                'pid': p.info['pid'],
                'name': p.info['name'],
                'rss_mb': round(p.info['memory_info'].rss / 1024 / 1024, 2) if p.info['memory_info'] else None,
                'mem_percent': round(p.info['memory_percent'], 2)
            }
            for p in top_procs
        ]
        # Info de plataforma
        platform_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
        }
        mem_breakdown = {
            'python_process': {
                'pid': process.pid,
                'rss_mb': round(mem_info.rss / 1024 / 1024, 2),
                'vms_mb': round(mem_info.vms / 1024 / 1024, 2),
                'percent': round(mem_percent, 2)
            },
            'system': {
                'total_mb': round(system_mem.total / 1024 / 1024, 2),
                'used_mb': round(system_mem.used / 1024 / 1024, 2),
                'percent': system_mem.percent
            },
            'swap': {
                'total_mb': round(swap_mem.total / 1024 / 1024, 2),
                'used_mb': round(swap_mem.used / 1024 / 1024, 2),
                'percent': swap_mem.percent
            },
            'top_processes': top_processes,
            'platform': platform_info
        }
        temp_files_list = list_temp_files()
        status_data = {
            "health": health_report,
            "uptime": uptime_str,
            "request_stats": request_stats,
            "database": monitoring._app_metrics["database_status"],
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory": mem_breakdown,
            "cache_stats": get_cache_stats(),
            "temp_files": temp_files_list
        }
        if full:
            status_data['raw_psutil'] = {
                'process': dict(mem_info._asdict()),
                'system': dict(system_mem._asdict()),
                'swap': dict(swap_mem._asdict()),
            }
        return status_data
    except Exception as e:
        logger.error(f"Error en get_system_status_data: {str(e)}", exc_info=True)
        return {
            "health": {"status": "error", "metrics": {"system_status": {"cpu_usage": 0, "memory_usage": {"used_mb": 0, "total_mb": 0}, "disk_usage": {"used_gb": 0, "total_gb": 0}}}},
            "uptime": "Error",
            "request_stats": {"total_requests": 0},
            "database": {"is_available": False, "response_time_ms": 0},
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory": {}
        }

from flask import jsonify, Blueprint, request

# ...

@admin_bp.route('/logs/list')
@admin_required
def logs_list():
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_files = get_log_files(logs_dir)
    return jsonify({'status': 'success', 'files': [f['name'] for f in log_files]})

def get_log_files(logs_dir):
    """Obtiene la lista de archivos de log disponibles (máx 20 más recientes)"""
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            return []
        log_files = []
        for file in os.listdir(logs_dir):
            if file.endswith('.log'):
                file_path = os.path.join(logs_dir, file)
                stats = os.stat(file_path)
                size_kb = stats.st_size / 1024
                mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                log_files.append({
                    'name': file,
                    'size': f"{size_kb:.2f} KB",
                    'modified': mod_time
                })
        # Ordenar y limitar a 20 más recientes
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        return log_files[:20]
    except Exception as e:
        logger.error(f"Error al obtener archivos de log: {str(e)}", exc_info=True)
        return []

def get_backup_files(backup_dir):
    """Obtiene la lista de archivos de backup disponibles (máx 20 más recientes, sin recursividad)"""
    try:
        logger.info(f"Buscando archivos de backup en: {backup_dir}")
        if not os.path.exists(backup_dir):
            logger.warning(f"El directorio de backups no existe: {backup_dir}")
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"Directorio de backups creado: {backup_dir}")
            return []
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith('.'):
                continue
            full_path = os.path.join(backup_dir, file)
            if not os.path.isfile(full_path):
                continue
            # Solo archivos de backup por extensión
            if not any(file.endswith(ext) for ext in ['.bak', '.backup', '.zip', '.tar', '.gz', '.sql', '.dump', '.old', '.back', '.tmp', '.swp', '~', '.csv', '.json']):
                continue
            stats = os.stat(full_path)
            size_bytes = stats.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes/1024:.2f} KB"
            else:
                size_str = f"{size_bytes/(1024*1024):.2f} MB"
            mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            backup_files.append({
                'name': file,
                'size': size_str,
                'modified': mod_time,
                'path': full_path
            })
        # Ordenar y limitar a 20 más recientes
        backup_files.sort(key=lambda x: x['modified'], reverse=True)
        return backup_files[:20]
    except Exception as e:
        logger.error(f"Error al obtener archivos de backup: {str(e)}", exc_info=True)
        return []

@admin_bp.route("/usuarios")
@admin_required
def lista_usuarios():
    try:
        # Obtener el término de búsqueda
        q = request.args.get('q', '').strip()
        users_col = get_users_collection()
        if q:
            # Búsqueda insensible a mayúsculas/minúsculas en email o nombre de usuario
            usuarios = list(users_col.find({
                "$or": [
                    {"email": {"$regex": q, "$options": "i"}},
                    {"username": {"$regex": q, "$options": "i"}},
                    {"nombre": {"$regex": q, "$options": "i"}}
                ]
            }))
        else:
            usuarios = list(users_col.find())
        # Ordenar usuarios por nombre alfabéticamente
        usuarios.sort(key=lambda u: u.get('nombre', '').lower())
        # Obtener catálogos para calcular cuántos tiene cada usuario
        from app.extensions import mongo
        collections_to_check = ['catalogs', 'spreadsheets']
        for user in usuarios:
            posibles = set([
                user.get("email"),
                user.get("username"),
                user.get("name"),
                user.get("nombre")
            ])
            posibles = {v for v in posibles if v}
            total_count = 0
            for collection_name in collections_to_check:
                try:
                    collection = mongo.db[collection_name]
                    query = {"$or": []}
                    for val in posibles:
                        query["$or"].extend([
                            {"created_by": val},
                            {"owner": val},
                            {"owner_name": val},
                            {"email": val},
                            {"username": val},
                            {"name": val}
                        ])
                    count = collection.count_documents(query)
                    total_count += count
                    logger.info(f"[ADMIN] Usuario {user.get('email')} tiene {count} catálogos en {collection_name}")
                except Exception as e:
                    logger.error(f"Error al contar catálogos en {collection_name}: {str(e)}")
            user["num_catalogs"] = total_count
            logger.info(f"[ADMIN] Usuario {user.get('email')} tiene un total de {total_count} catálogos")
        # Calcular estadísticas
        stats = {
            "total": len(usuarios),
            "roles": {
                "admin": sum(1 for u in usuarios if u.get("role") == "admin"),
                "normal": sum(1 for u in usuarios if u.get("role") == "user"),
                "no_role": sum(1 for u in usuarios if not u.get("role"))
            }
        }
        return render_template("admin/users.html", usuarios=usuarios, stats=stats)
    except Exception as e:
        logger.error(f"Error en lista_usuarios: {str(e)}", exc_info=True)
        flash(f"Error al cargar la lista de usuarios: {str(e)}", "error")
        return redirect(url_for('admin.dashboard_admin'))

@admin_bp.route("/usuarios/<user_email>/catalogos")
@admin_required
def ver_catalogos_usuario(user_email):
    try:
        # Verificar que el usuario existe
        user = get_users_collection().find_one({"email": user_email})
        if not user:
            flash(f"Usuario con email {user_email} no encontrado", "error")
            return redirect(url_for('admin.lista_usuarios'))
        # Unificar criterio: buscar por todos los posibles identificadores
        posibles = set([
            user.get("email"),
            user.get("username"),
            user.get("name"),
            user.get("nombre")
        ])
        posibles = {v for v in posibles if v}
        from app.extensions import mongo
        collections_to_check = ['catalogs', 'spreadsheets']
        all_catalogs = []
        for collection_name in collections_to_check:
            try:
                collection = mongo.db[collection_name]
                query = {"$or": []}
                for val in posibles:
                    query["$or"].extend([
                        {"created_by": val},
                        {"owner": val},
                        {"owner_name": val},
                        {"email": val},
                        {"username": val},
                        {"name": val}
                    ])
                catalogs_cursor = collection.find(query)
                for catalog in catalogs_cursor:
                    catalog['collection_source'] = collection_name
                    all_catalogs.append(catalog)
                logger.info(f"[ADMIN] Encontrados {collection.count_documents(query)} catálogos en {collection_name} para {posibles}")
            except Exception as e:
                logger.error(f"Error al buscar catálogos en {collection_name}: {str(e)}")
        catalogs = all_catalogs
        logger.info(f"[ADMIN] Total de catálogos encontrados para {posibles}: {len(catalogs)}")
        # Añadir _id_str a cada catálogo para facilitar su uso en las plantillas
        for catalog in catalogs:
            catalog['_id_str'] = str(catalog['_id'])
            # Calcular el número de filas del catálogo
            if 'rows' in catalog:
                catalog['row_count'] = len(catalog['rows'])
            elif 'data' in catalog:
                catalog['row_count'] = len(catalog['data'])
            else:
                catalog['row_count'] = 0
            # Formatear la fecha de creación
            if 'created_at' in catalog and catalog['created_at']:
                if isinstance(catalog['created_at'], str):
                    catalog['created_at_formatted'] = catalog['created_at']
                else:
                    catalog['created_at_formatted'] = catalog['created_at'].strftime('%d/%m/%Y %H:%M')
            else:
                catalog['created_at_formatted'] = 'N/A'
        return render_template("admin/catalogos_usuario.html", user=user, catalogs=catalogs)
    except Exception as e:
        logger.error(f"Error en ver_catalogos_usuario: {str(e)}", exc_info=True)
        flash(f"Error al cargar los catálogos del usuario: {str(e)}", "error")
        # Intentar recuperar el usuario incluso en caso de error
        try:
            user = get_users_collection().find_one({"email": user_email})
            if user:
                return render_template("admin/catalogos_usuario.html", user=user, catalogs=[])
        except Exception as inner_e:
            logger.error(f"Error secundario al recuperar usuario: {str(inner_e)}")
        return redirect(url_for("admin.lista_usuarios"))

@admin_bp.route("/usuarios/catalogo/<catalog_id>")
@admin_required
def ver_catalogo_admin(catalog_id):
    try:
        # Obtener el catálogo
        from app.extensions import mongo
        from bson.objectid import ObjectId
        
        catalog = mongo.db.catalogs.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            flash(f"Catálogo con ID {catalog_id} no encontrado", "error")
            return redirect(url_for('admin.lista_usuarios'))
        
        # Añadir _id_str al catálogo
        catalog['_id_str'] = str(catalog['_id'])
        
        return render_template("admin/ver_catalogo.html", catalog=catalog)
    except Exception as e:
        logger.error(f"Error en ver_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al cargar el catálogo: {str(e)}", "error")
        return redirect(url_for('admin.lista_usuarios'))

@admin_bp.route("/usuarios/delete/<user_id>", methods=["POST"])
@admin_required
def eliminar_usuario(user_id):
    get_users_collection().delete_one({"_id": ObjectId(user_id)})
    flash("Usuario eliminado", "success")
    return redirect(url_for("admin.lista_usuarios"))

@admin_bp.route("/usuarios/edit/<user_id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(user_id):
    try:
        users_col = get_users_collection()
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("admin.lista_usuarios"))

        if request.method == "POST":
            # Verificar si es una solicitud de verificación desde la página verify_users
            verified = request.form.get("verified")
            if verified == "true":
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"verified": True, "updated_at": datetime.now()}}
                )
                flash(f"Usuario {user.get('nombre', 'desconocido')} ha sido verificado", "success")
                # Registrar en el log de auditoría
                audit_log(f"Usuario {user.get('email')} verificado por {session.get('username')}")
                return redirect(url_for("admin.verify_users"))
                
            # Procesamiento normal de edición de usuario
            nombre = request.form.get("nombre")
            email = request.form.get("email")
            role = request.form.get("role", "user")
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            verified_status = request.form.get("verified_status") == "on"

            # Validar que el nombre y email no estén vacíos
            if not nombre or not email:
                flash("El nombre y el correo son requeridos", "error")
                return redirect(url_for("admin.editar_usuario", user_id=user_id))
            
            # Verificar si el email ya existe para otro usuario
            email_changed = email.lower() != user.get('email', '').lower()
            email_conflict = False
            
            if email_changed:
                # Buscar si el email ya existe para otro usuario
                existing_user = users_col.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})
                
                if existing_user and str(existing_user.get('_id')) != user_id:
                    email_conflict = True
                    flash(f"El correo electrónico {email} ya está en uso por otro usuario", "error")
                    logger.warning(f"Intento de actualizar usuario {user_id} con email duplicado: {email}")

            # Si se proporcionó una nueva contraseña
            if new_password:
                if new_password != confirm_password:
                    flash("Las contraseñas no coinciden", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Verificar que la contraseña cumpla con los requisitos
                if len(new_password) < 8:
                    flash("La contraseña debe tener al menos 8 caracteres", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Actualizar la contraseña
                password_hash = generate_password_hash(new_password)
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"password": password_hash}}
                )
                flash("Contraseña actualizada", "success")

            # Si hay conflicto de email, no actualizar nada más
            if email_conflict:
                return redirect(url_for("admin.editar_usuario", user_id=user_id))

            # Actualizar otros campos
            update_data = {
                "nombre": nombre,
                "role": role,
                "verified": verified_status,
                "updated_at": datetime.now()
            }
            
            # Solo actualizar el email si ha cambiado
            if email_changed:
                update_data["email"] = email
            
            # Realizar la actualización
            users_col.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for("admin.lista_usuarios"))

        return render_template("admin/editar_usuario.html", usuario=user)
    except Exception as e:
        logger.error(f"Error al editar usuario {user_id}: {str(e)}", exc_info=True)
        flash(f"Error al editar usuario: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))

@admin_bp.route("/usuarios/create", methods=["GET", "POST"])
@admin_required
def crear_usuario():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "user")
        
        if not all([nombre, email, password]):
            flash("Todos los campos son requeridos", "error")
            return render_template("admin/crear_usuario.html")
            
        users_col = get_users_collection()
        existing_user = users_col.find_one({"email": email})
        
        if existing_user:
            flash("Ya existe un usuario con este email", "error")
            return render_template("admin/crear_usuario.html")
            
        # Aquí deberías implementar la lógica para hashear la contraseña
        # Por ahora, usaremos el password directamente
        user_data = {
            "nombre": nombre,
            "email": email,
            "password": password,  # En producción, hashea esto
            "role": role,
            "num_tables": 0,
            "tables_updated_at": None,
            "last_ip": "",
            "last_login": None,
            "updated_at": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        
        users_col.insert_one(user_data)
        flash("Usuario creado exitosamente", "success")
        return redirect(url_for("admin.lista_usuarios"))
    
    return render_template("admin/crear_usuario.html")

@admin_bp.route("/backup/json")
def backup_json():
    from datetime import datetime
    import tempfile
    catalog = get_catalogs_collection()
    data = list(catalog.find())
    for d in data:
        d["_id"] = str(d["_id"])
    output = io.StringIO()
    json.dump(data, output, indent=4, default=str)
    output.seek(0)
    # Guardar el archivo en /backups/ con nombre único
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir, exist_ok=True)
    filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = os.path.join(backups_dir, filename)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    # Subir a Google Drive
    try:
        enlace_drive = upload_to_drive(backup_path)
        os.remove(backup_path)
        flash(f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>", "success")
        audit_log(f"Backup JSON subido a Drive por {session.get('user_id', session.get('username', 'desconocido'))} - {filename}")
    except Exception as e:
        flash(f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.", "danger")
        audit_log(f"Backup JSON local por {session.get('user_id', session.get('username', 'desconocido'))} - {filename} (fallo subida Drive: {str(e)})")
    # Permitir descarga directa como antes
    return send_file(io.BytesIO(output.read().encode()), download_name="backup_catalog.json", as_attachment=True)

@admin_bp.route("/backup/csv")
def backup_csv():
    import tempfile
    from datetime import datetime
    catalog = get_catalogs_collection()
    data = list(catalog.find())
    if not data:
        flash("No hay datos para exportar", "warning")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    # Unificar todos los campos presentes en los documentos
    all_fields = set()
    for row in data:
        all_fields.update(row.keys())
    headers = list(all_fields)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in data:
        row["_id"] = str(row["_id"])
        row_filled = {k: row.get(k, "") for k in headers}
        writer.writerow(row_filled)
    output.seek(0)
    # Guardar el archivo en /backups/ con nombre único
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir, exist_ok=True)
    filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    backup_path = os.path.join(backups_dir, filename)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    # Subir a Google Drive
    try:
        enlace_drive = upload_to_drive(backup_path)
        os.remove(backup_path)
        flash(f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>", "success")
        audit_log(f"Backup CSV subido a Drive por {session.get('user_id', session.get('username', 'desconocido'))} - {filename}")
    except Exception as e:
        flash(f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.", "danger")
        audit_log(f"Backup CSV local por {session.get('user_id', session.get('username', 'desconocido'))} - {filename} (fallo subida Drive: {str(e)})")
    # Permitir descarga directa como antes
    return send_file(io.BytesIO(output.read().encode()), download_name="backup_catalog.csv", as_attachment=True)

@admin_bp.route("/backups/cleanup", methods=["POST"])
@admin_required
def cleanup_old_backups():
    """Elimina backups antiguos según la fecha o cantidad máxima permitida."""
    days = int(request.form.get("days", 30))
    max_files = int(request.form.get("max_files", 20))
    backups_dir = os.path.join(os.getcwd(), "backups")
    if not os.path.exists(backups_dir):
        flash("No hay backups para limpiar", "info")
        return redirect(url_for("maintenance.maintenance_dashboard"))
    files = [os.path.join(backups_dir, f) for f in os.listdir(backups_dir) if os.path.isfile(os.path.join(backups_dir, f))]
    # Ordenar por fecha de modificación descendente
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    now = datetime.now()
    removed = 0
    # Eliminar archivos más antiguos que X días
    for f in files:
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        if (now - mtime) > timedelta(days=days):
            try:
                os.remove(f)
                removed += 1
                logger.info(f"Backup eliminado por antigüedad: {f}")
            except Exception as e:
                logger.error(f"Error al eliminar backup {f}: {e}")
    # Si hay más de max_files, eliminar los más antiguos
    files = [os.path.join(backups_dir, f) for f in os.listdir(backups_dir) if os.path.isfile(os.path.join(backups_dir, f))]
    if len(files) > max_files:
        for f in files[max_files:]:
            try:
                os.remove(f)
                removed += 1
                logger.info(f"Backup eliminado por exceso de cantidad: {f}")
            except Exception as e:
                logger.error(f"Error al eliminar backup {f}: {e}")
    flash(f"Backups antiguos eliminados: {removed}", "info")
    audit_log(f"Limpieza de backups por {session.get('user_id', session.get('username', 'desconocido'))} - días: {days}, max_files: {max_files}, eliminados: {removed}")
    return redirect(url_for("maintenance.maintenance_dashboard"))

@admin_bp.route("/cleanup_resets")
@admin_required
def cleanup_resets():
    result = get_reset_tokens_collection().delete_many({"used": True})
    flash(f"Tokens eliminados: {result.deleted_count}", "info")
    
    # Registrar la limpieza en las métricas
    if "cleanup_history" not in monitoring._app_metrics:
        monitoring._app_metrics["cleanup_history"] = []
    
    monitoring._app_metrics["cleanup_history"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "tokens_reset",
        "count": result.deleted_count
    })
    monitoring.save_metrics()
    
    return redirect(url_for("maintenance.maintenance_dashboard"))

# API para limpieza de archivos temporales antiguos
@admin_bp.route("/delete-temp-files", methods=["POST"])
@admin_required
def delete_temp_files_route():
    selected = request.form.getlist('temp_files')
    if not selected:
        flash("No se seleccionaron archivos para borrar", "warning")
        return redirect(url_for('admin.system_status'))
    removed = delete_temp_files(selected)
    flash(f"Archivos temporales eliminados: {removed}", "success")
    return redirect(url_for('admin.system_status'))

@admin_bp.route("/api/cleanup-temp", methods=["POST"])
@admin_required
def api_cleanup_temp():
    days = request.form.get("days", 7, type=int)
    result = monitoring.cleanup_old_temp_files(days)
    
    # Registrar la limpieza en las métricas
    if "cleanup_history" not in monitoring._app_metrics:
        monitoring._app_metrics["cleanup_history"] = []
    
    monitoring._app_metrics["cleanup_history"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "temp_files",
        "days": days,
        "files_removed": result.get("files_removed", 0),
        "bytes_removed": result.get("bytes_removed", 0)
    })
    monitoring.save_metrics()
    
    return jsonify({
        "success": True,
        "message": f"Se eliminaron {result.get('files_removed', 0)} archivos temporales",
        "details": result
    })

# API para obtener el estado del sistema
@admin_bp.route("/api/system-status")
@admin_required
def api_system_status():
    try:
        # Obtener métricas del sistema
        monitoring.check_system_health()
        
        # Preparar respuesta
        response = {
            "status": "success",
            "data": monitoring._app_metrics
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error en api_system_status: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)})

# API para truncar archivos de log
@admin_bp.route("/api/truncate-logs", methods=["POST"])
@admin_required
def api_truncate_logs():
    try:
        # Obtener datos de la solicitud
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No se proporcionaron datos"})
        
        log_files = data.get("logFiles", [])
        method = data.get("method", "complete")
        
        if not log_files:
            return jsonify({"status": "error", "message": "No se especificaron archivos de log"})
        
        # Verificar que los archivos existen y son válidos
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
        processed_files = []
        error_files = []
        
        for log_file in log_files:
            # Validar el nombre del archivo para evitar ataques de traversal de directorio
            if '..' in log_file or '/' in log_file or '\\' in log_file:
                error_files.append(f"{log_file} (nombre de archivo no válido)")
                continue
            
            log_path = os.path.join(logs_dir, log_file)
            if not os.path.exists(log_path):
                error_files.append(f"{log_file} (no existe)")
                continue
            
            try:
                if method == "complete":
                    # Truncado completo
                    with open(log_path, 'w') as f:
                        f.truncate(0)
                    processed_files.append(log_file)
                    logger.info(f"Archivo de log {log_file} truncado completamente")
                    
                elif method == "lines":
                    # Mantener últimas N líneas
                    try:
                        line_count = int(data.get("lineCount", 100))
                        if line_count < 10:
                            line_count = 10  # Mínimo 10 líneas
                    except (ValueError, TypeError):
                        line_count = 100  # Valor predeterminado si hay un error
                    
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        # Mantener solo las últimas N líneas
                        if len(lines) > line_count:
                            with open(log_path, 'w', encoding='utf-8') as f:
                                f.writelines(lines[-line_count:])
                            logger.info(f"Archivo de log {log_file} truncado a las últimas {line_count} líneas")
                        else:
                            logger.info(f"El archivo {log_file} tiene menos de {line_count} líneas, no se truncó")
                        
                        processed_files.append(log_file)
                    except UnicodeDecodeError:
                        # Si hay problemas con la codificación, usar un enfoque binario
                        with open(log_path, 'rb') as f:
                            f.seek(0, os.SEEK_END)
                            size = f.tell()
                            
                            # Estimar el tamaño promedio de línea (100 bytes)
                            avg_line_size = 100
                            estimated_size = line_count * avg_line_size
                            
                            # Si el archivo es más grande que el tamaño estimado, truncarlo
                            if size > estimated_size:
                                # Retroceder aproximadamente el número de líneas deseado
                                f.seek(-min(size, estimated_size * 2), os.SEEK_END)
                                # Leer el resto del archivo
                                data = f.read()
                                
                                # Contar nuevas líneas y ajustar si es necesario
                                newlines = data.count(b'\n')
                                if newlines > line_count:
                                    # Encontrar la posición de la línea de inicio
                                    pos = 0
                                    for i in range(newlines - line_count):
                                        next_pos = data.find(b'\n', pos) + 1
                                        if next_pos == 0:  # No se encontró
                                            break
                                        pos = next_pos
                                    
                                    # Escribir solo las últimas líneas
                                    with open(log_path, 'wb') as f:
                                        f.write(data[pos:])
                                    
                                    logger.info(f"Archivo de log {log_file} truncado a aproximadamente las últimas {line_count} líneas (modo binario)")
                                    processed_files.append(log_file)
                                else:
                                    logger.info(f"El archivo {log_file} tiene menos de {line_count} líneas, no se truncó")
                                    processed_files.append(log_file)
                    
                elif method == "date":
                    # Eliminar entradas anteriores a una fecha
                    cutoff_date = data.get("cutoffDate")
                    if not cutoff_date:
                        error_files.append(f"{log_file} (no se especificó fecha de corte)")
                        continue
                    
                    # Convertir la fecha a un objeto datetime
                    try:
                        cutoff_date = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
                    except ValueError:
                        error_files.append(f"{log_file} (formato de fecha inválido, use YYYY-MM-DD)")
                        continue
                    
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        # Filtrar líneas por fecha
                        kept_lines = []
                        for line in lines:
                            # Intentar extraer la fecha de la línea de log (formato típico: [YYYY-MM-DD HH:MM:SS,mmm])
                            date_match = re.search(r'\[(\d{4}-\d{2}-\d{2})', line)
                            if date_match:
                                try:
                                    line_date_str = date_match.group(1)
                                    line_date = datetime.strptime(line_date_str, "%Y-%m-%d").date()
                                    if line_date >= cutoff_date:
                                        kept_lines.append(line)
                                except ValueError:
                                    # Si hay un error al parsear la fecha, mantener la línea
                                    kept_lines.append(line)
                            else:
                                # Si no se puede extraer la fecha, mantener la línea
                                kept_lines.append(line)
                        
                        # Escribir las líneas filtradas de vuelta al archivo
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.writelines(kept_lines)
                        
                        logger.info(f"Archivo de log {log_file} truncado a entradas posteriores a {cutoff_date}")
                        processed_files.append(log_file)
                    except UnicodeDecodeError:
                        error_files.append(f"{log_file} (error de codificación, no se puede procesar por fecha)")
                        continue
                    
                else:
                    error_files.append(f"{log_file} (método de truncado no válido)")
                    continue
                    
            except Exception as e:
                logger.error(f"Error al truncar el archivo {log_file}: {str(e)}", exc_info=True)
                error_files.append(f"{log_file} (error: {str(e)})")
        
        # Registrar en el log de auditoría
        audit_log(f"Truncado de logs: {', '.join(processed_files)} usando método {method}")
        
        # Preparar respuesta
        if error_files:
            return jsonify({
                "status": "partial",
                "message": f"Se procesaron {len(processed_files)} archivos con éxito. Errores en {len(error_files)} archivos.",
                "processed": processed_files,
                "error_files": error_files
            })
        else:
            return jsonify({
                "status": "success",
                "message": f"Se truncaron {len(processed_files)} archivos de log correctamente.",
                "processed": processed_files,
                "error_files": []
            })
            
    except Exception as e:
        logger.error(f"Error en api_truncate_logs: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error al truncar logs: {str(e)}", "error_files": []})

# API para eliminar archivos de backup
@admin_bp.route("/api/delete-backups", methods=["POST"])
@admin_required
def api_delete_backups():
    try:
        # Obtener datos de la solicitud
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No se proporcionaron datos"})
        
        backup_files = data.get("backupFiles", [])
        delete_criteria = data.get("deleteCriteria", "selected")
        
        if delete_criteria == "selected" and not backup_files:
            from flask import abort
            abort(400, description="No se especificaron archivos de backup para eliminar")
        
        # Verificar que los archivos existen y son válidos
        backup_dir = os.path.abspath(os.path.join(os.getcwd(), 'backups'))
        logger.info(f"API Delete - Directorio de backups: {backup_dir}")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        processed_files = []
        error_files = []
        
        # Obtener todos los archivos de backup si el criterio es por fecha o todos
        all_backup_files = []
        if delete_criteria in ["date", "all"]:
            all_backup_files = get_backup_files(backup_dir)
        
        if delete_criteria == "selected":
            # Eliminar archivos seleccionados
            for backup_file in backup_files:
                # Validar el nombre del archivo para evitar ataques de traversal de directorio
                if '..' in backup_file:
                    error_files.append(f"{backup_file} (nombre de archivo no válido)")
                    continue
                
                # Manejar archivos en subdirectorios
                backup_path = os.path.join(backup_dir, backup_file)
                if not os.path.exists(backup_path):
                    error_files.append(f"{backup_file} (no existe)")
                    continue
                
                try:
                    os.remove(backup_path)
                    processed_files.append(backup_file)
                    logger.info(f"Archivo de backup {backup_file} eliminado correctamente")
                except Exception as e:
                    logger.error(f"Error al eliminar el archivo {backup_file}: {str(e)}", exc_info=True)
                    error_files.append(f"{backup_file} (error: {str(e)})")
        
        elif delete_criteria == "date":
            # Eliminar archivos anteriores a una fecha
            cutoff_date = data.get("cutoffDate")
            if not cutoff_date:
                return jsonify({"status": "error", "message": "No se especificó fecha de corte"})
            
            try:
                cutoff_date = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"status": "error", "message": "Formato de fecha inválido, use YYYY-MM-DD"})
            
            for backup_file in all_backup_files:
                try:
                    file_date = datetime.strptime(backup_file['modified'], "%Y-%m-%d %H:%M:%S").date()
                    if file_date < cutoff_date:
                        os.remove(backup_file['path'])
                        processed_files.append(backup_file['name'])
                        logger.info(f"Archivo de backup {backup_file['name']} eliminado (anterior a {cutoff_date})")
                except Exception as e:
                    logger.error(f"Error al procesar el archivo {backup_file['name']}: {str(e)}", exc_info=True)
                    error_files.append(f"{backup_file['name']} (error: {str(e)})")
        
        elif delete_criteria == "all":
            # Eliminar todos los archivos de backup
            for backup_file in all_backup_files:
                try:
                    os.remove(backup_file['path'])
                    processed_files.append(backup_file['name'])
                    logger.info(f"Archivo de backup {backup_file['name']} eliminado (eliminación total)")
                except Exception as e:
                    logger.error(f"Error al eliminar el archivo {backup_file['name']}: {str(e)}", exc_info=True)
                    error_files.append(f"{backup_file['name']} (error: {str(e)})")
        
        else:
            return jsonify({"status": "error", "message": f"Criterio de eliminación no válido: {delete_criteria}"})
        
        # Registrar en el log de auditoría
        audit_log(f"Eliminación de backups: {', '.join(processed_files)} usando criterio {delete_criteria}")
        
        # Preparar respuesta
        if error_files:
            return jsonify({
                "status": "partial",
                "message": f"Se eliminaron {len(processed_files)} archivos, pero hubo errores con {len(error_files)} archivos",
                "processed": processed_files,
                "error_files": error_files
            })
        else:
            return jsonify({
                "status": "success",
                "message": f"Se eliminaron {len(processed_files)} archivos correctamente",
                "processed": processed_files,
                "error_files": []
            })
    
    except Exception as e:
        logger.error(f"Error en api_delete_backups: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error al procesar la solicitud: {str(e)}"})

# Ruta para descargar un archivo de log específico
@admin_bp.route("/logs/download/<filename>")
@admin_required
def download_log(filename):
    try:
        # Validar el nombre del archivo
        if '..' in filename or '/' in filename or '\\' in filename:
            flash("Nombre de archivo no válido", "danger")
            return redirect(url_for("admin.system_status"))
        
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
        log_path = os.path.join(logs_dir, filename)
        
        if not os.path.exists(log_path):
            flash(f"El archivo {filename} no existe", "danger")
            return redirect(url_for("admin.system_status"))
        
        # Registrar en el log de auditoría
        audit_log(f"Descarga de archivo de log: {filename}")
        
        return send_file(log_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error al descargar log {filename}: {str(e)}", exc_info=True)
        flash(f"Error al descargar el archivo: {str(e)}", "danger")
        return redirect(url_for("admin.system_status"))

# Ruta para descargar múltiples archivos de log en un ZIP
@admin_bp.route("/logs/download-multiple")
@admin_required
def download_multiple_logs():
    try:
        files_param = request.args.get("files", "")
        if not files_param:
            flash("No se especificaron archivos para descargar", "danger")
            return redirect(url_for("admin.system_status"))
        
        files = files_param.split(",")
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
        
        # Crear un archivo ZIP temporal
        import tempfile
        import zipfile
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_file.close()
        
        with zipfile.ZipFile(temp_file.name, 'w') as zipf:
            for filename in files:
                # Validar el nombre del archivo
                if '..' in filename or '/' in filename or '\\' in filename:
                    continue
                
                log_path = os.path.join(logs_dir, filename)
                if os.path.exists(log_path):
                    zipf.write(log_path, arcname=filename)
        
        # Registrar en el log de auditoría
        audit_log(f"Descarga de múltiples archivos de log: {', '.join(files)}")
        
        return send_file(temp_file.name, as_attachment=True, download_name="logs.zip")
    except Exception as e:
        logger.error(f"Error al descargar múltiples logs: {str(e)}", exc_info=True)
        flash(f"Error al descargar los archivos: {str(e)}", "danger")
        return redirect(url_for("admin.system_status"))

@admin_bp.route("/notification-settings", methods=["GET", "POST"])
@admin_required
def notification_settings():
    """Página de configuración de notificaciones"""
    if request.method == "POST":
        # Validar campos obligatorios y tipos
        required_fields = [
            "smtp_server", "smtp_port", "smtp_username",
            "threshold_cpu", "threshold_memory", "threshold_disk", "threshold_error_rate", "cooldown"
        ]
        missing_fields = [f for f in required_fields if not request.form.get(f)]
        int_fields = ["smtp_port", "threshold_cpu", "threshold_memory", "threshold_disk", "threshold_error_rate", "cooldown"]
        invalid_ints = []
        for f in int_fields:
            val = request.form.get(f)
            if val is not None and val != "":
                try:
                    int(val)
                except Exception:
                    invalid_ints.append(f)
            else:
                invalid_ints.append(f)
        if missing_fields or invalid_ints:
            flash(f"Error: Faltan campos obligatorios o valores inválidos: {', '.join(set(missing_fields + invalid_ints))}", "danger")
            return redirect(url_for("admin.notification_settings"))

        enabled = request.form.get("enable_notifications") == "on"
        smtp_settings = {
            "server": request.form.get("smtp_server"),
            "port": int(request.form.get("smtp_port")),
            "username": request.form.get("smtp_username"),
            "use_tls": request.form.get("smtp_tls") == "on"
        }
        password = request.form.get("smtp_password")
        if password:
            smtp_settings["password"] = password
        recipients = [r for r in request.form.getlist("recipients") if r.strip()]
        thresholds = {
            "cpu": int(request.form.get("threshold_cpu")),
            "memory": int(request.form.get("threshold_memory")),
            "disk": int(request.form.get("threshold_disk")),
            "error_rate": int(request.form.get("threshold_error_rate"))
        }
        cooldown = int(request.form.get("cooldown"))
        if notifications.update_settings(
            enabled=enabled,
            smtp_settings=smtp_settings,
            recipients=recipients,
            thresholds=thresholds,
            cooldown=cooldown
        ):
            flash("Configuración de notificaciones actualizada correctamente", "success")
            audit_log("notification_settings_updated", details={
                "enabled": enabled,
                "smtp_server": smtp_settings["server"],
                "recipients_count": len(recipients)
            })
        else:
            flash("Error al guardar la configuración de notificaciones", "danger")
        return redirect(url_for("admin.notification_settings"))
    config = notifications.get_settings()
    return render_template("admin/notification_settings.html", config=config)

@admin_bp.route("/api/test-email", methods=["POST"])
@admin_required
def test_email():
    """Enviar correo de prueba usando las credenciales del archivo .env"""
    email = request.form.get("email")
    if not email:
        return jsonify({"success": False, "error": "No se proporcionó dirección de correo"})
    
    try:
        # Registrar información sobre el intento de envío
        logger.info(f"[ADMIN] Intentando enviar correo de prueba a {email}")
        
        # Mostrar las variables de entorno relacionadas con el correo (sin la contraseña)
        mail_server = os.environ.get('MAIL_SERVER')
        mail_port = os.environ.get('MAIL_PORT')
        mail_username = os.environ.get('MAIL_USERNAME')
        mail_use_tls = os.environ.get('MAIL_USE_TLS')
        mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')
        mail_default_sender_name = os.environ.get('MAIL_DEFAULT_SENDER_NAME')
        mail_default_sender_email = os.environ.get('MAIL_DEFAULT_SENDER_EMAIL')
        
        logger.info(f"[ADMIN] Configuración de correo: Servidor={mail_server}, Puerto={mail_port}, "  
                   f"Usuario={mail_username}, TLS={mail_use_tls}")
        logger.info(f"[ADMIN] Remitentes configurados: DEFAULT_SENDER={mail_default_sender}, "  
                   f"SENDER_NAME={mail_default_sender_name}, SENDER_EMAIL={mail_default_sender_email}")
        
        # Crear un correo de prueba extremadamente simple para diagnosticar el problema
        import smtplib
        from email.mime.text import MIMEText
        
        try:
            # Crear un mensaje simple de texto plano
            logger.info("[ADMIN] Creando mensaje de prueba simple...")
            msg = MIMEText("Este es un mensaje de prueba.")
            msg['Subject'] = "Prueba de correo desde edefrutos2025"
            msg['From'] = mail_username
            msg['To'] = email
            
            # Intentar enviar directamente
            logger.info(f"[ADMIN] Conectando a {mail_server}:{mail_port}...")
            server = smtplib.SMTP(mail_server, int(mail_port))
            
            if mail_use_tls and mail_use_tls.lower() in ('true', '1', 't'):
                logger.info("[ADMIN] Iniciando TLS...")
                server.starttls()
            
            logger.info(f"[ADMIN] Iniciando sesión con {mail_username}...")
            server.login(mail_username, os.environ.get('MAIL_PASSWORD'))
            
            logger.info("[ADMIN] Enviando mensaje...")
            server.send_message(msg)
            
            logger.info("[ADMIN] Cerrando conexión...")
            server.quit()
            
            logger.info(f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método directo")
            audit_log("test_email_sent", details={"recipient": email, "method": "direct"})
            return jsonify({"success": True})
        except Exception as direct_err:
            logger.error(f"[ADMIN] Error en método directo: {str(direct_err)}", exc_info=True)
            
            # Si el método directo falla, intentar con el método normal
            logger.info("[ADMIN] Intentando con el método normal...")
            result = notifications.send_test_email(email)
            
            if result:
                logger.info(f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método normal")
                audit_log("test_email_sent", details={"recipient": email, "method": "normal"})
                return jsonify({"success": True})
            else:
                logger.error(f"[ADMIN] Error al enviar correo de prueba a {email}. Ambos métodos fallaron.")
                return jsonify({"success": False, "error": f"Error directo: {str(direct_err)}. Error en método normal: Resultado falso sin excepción. Revisa los logs para más detalles."})
    except Exception as e:
        logger.error(f"[ADMIN] Excepción al enviar correo de prueba a {email}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Error: {str(e)}"})

@admin_bp.route("/verify-users")
@admin_required
def verify_users():
    try:
        usuarios = list(get_users_collection().find())
        # Contar usuarios verificados y no verificados
        verified_count = sum(1 for user in usuarios if user.get('verified', False))
        unverified_count = len(usuarios) - verified_count
        # Estadísticas de usuarios
        stats = {
            'total': len(usuarios),
            'verified': verified_count,
            'unverified': unverified_count
        }
        # Obtener usuarios no verificados para mostrarlos en la interfaz
        unverified_users = [user for user in usuarios if not user.get('verified', False)]
        return render_template('admin/verify_users.html', stats=stats, unverified_users=unverified_users)
    except Exception as e:
        logger.error(f"Error en verify_users: {str(e)}", exc_info=True)
        flash(f"Error al verificar usuarios: {str(e)}", "error")
        return redirect(url_for('maintenance.maintenance_dashboard'))

@admin_bp.route("/bulk_user_action", methods=["POST"])
@admin_required
def bulk_user_action():
    try:
        user_ids = request.form.getlist("user_ids")
        action = request.form.get("action")
        users_col = get_users_collection()
        if not user_ids or not action:
            flash("Debes seleccionar usuarios y una acción.", "warning")
            return redirect(url_for("admin.verify_users"))
        from bson import ObjectId
        object_ids = [ObjectId(uid) for uid in user_ids if uid]
        if action == "verify":
            result = users_col.update_many({"_id": {"$in": object_ids}}, {"$set": {"verified": True}})
            flash(f"{result.modified_count} usuarios verificados.", "success")
        elif action == "delete":
            result = users_col.delete_many({"_id": {"$in": object_ids}})
            flash(f"{result.deleted_count} usuarios eliminados.", "success")
        else:
            flash("Acción no reconocida.", "danger")
        return redirect(url_for("admin.verify_users"))
    except Exception as e:
        logger.error(f"Error en bulk_user_action: {str(e)}", exc_info=True)
        flash(f"Error al procesar la acción masiva: {str(e)}", "danger")
        return redirect(url_for("admin.verify_users"))

@admin_bp.route("/catalogos-usuario/<user_id>")
@admin_required
def ver_catalogos_usuario_por_id(user_id):
    try:
        # Verificar que el usuario existe
        usuario = get_users_collection().find_one({"_id": ObjectId(user_id)})
        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for("admin.lista_usuarios"))

        # Obtener todos los posibles identificadores del usuario
        user_email = usuario.get("email", "")
        username = usuario.get("username", "")
        nombre = usuario.get("name", "")
        posibles = set([user_email, username, nombre])
        posibles = {v for v in posibles if v}
        logger.info(f"[ADMIN] Buscando catálogos para el usuario con ID: {user_id}, posibles: {posibles}")

        # Obtener los catálogos del usuario de ambas colecciones
        collections_to_check = ['catalogs', 'spreadsheets']
        all_catalogs = []

        for collection_name in collections_to_check:
            try:
                collection = get_db()[collection_name]
                # Buscar por todos los campos posibles
                query = {"$or": []}
                for val in posibles:
                    query["$or"].extend([
                        {"created_by": val},
                        {"owner": val},
                        {"owner_name": val},
                        {"email": val},
                        {"username": val},
                        {"name": val}
                    ])
                catalogs_cursor = collection.find(query)
                for catalog in catalogs_cursor:
                    catalog['collection_source'] = collection_name
                    catalog['_id_str'] = str(catalog['_id'])
                    all_catalogs.append(catalog)
                logger.info(f"[ADMIN] Encontrados {collection.count_documents(query)} catálogos en {collection_name} para {posibles}")
            except Exception as e:
                logger.error(f"Error al buscar catálogos en {collection_name}: {str(e)}")

        catalogs = all_catalogs
        logger.info(f"[ADMIN] Total de catálogos encontrados para {posibles}: {len(catalogs)}")

        # Añadir información adicional a cada catálogo
        for catalog in catalogs:
            if 'rows' in catalog and catalog['rows'] is not None:
                catalog['row_count'] = len(catalog['rows'])
            elif 'data' in catalog and catalog['data'] is not None:
                catalog['row_count'] = len(catalog['data'])
            else:
                catalog['row_count'] = 0
            if "created_at" in catalog and catalog["created_at"]:
                try:
                    if hasattr(catalog["created_at"], "strftime"):
                        catalog["created_at_formatted"] = catalog["created_at"].strftime("%d/%m/%Y %H:%M")
                    else:
                        catalog["created_at_formatted"] = str(catalog["created_at"])
                except Exception as e:
                    logger.error(f"Error al formatear fecha: {str(e)}")
                    catalog["created_at_formatted"] = str(catalog["created_at"])
            else:
                catalog["created_at_formatted"] = "Fecha desconocida"

        return render_template("admin/catalogos_usuario.html", catalogs=catalogs, user=usuario)
    except Exception as e:
        logger.error(f"Error en ver_catalogos_usuario: {str(e)}", exc_info=True)
        flash(f"Error al cargar los catálogos del usuario: {str(e)}", "error")
        return redirect(url_for('admin.lista_usuarios'))

@admin_bp.route("/catalogo/<collection_source>/<catalog_id>")
@admin_required
def ver_catalogo_unificado(collection_source, catalog_id):
    logger.info(f"[ADMIN] Entrando en ver_catalogo_unificado con collection_source={collection_source}, catalog_id={catalog_id}")
    try:
        db = get_db()
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            logger.warning(f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}")
            flash("Catálogo no encontrado", "warning")
            return render_template("admin/ver_catalogo.html", catalog=None, error="Catálogo no encontrado")
        # Refuerzo: asegurar que headers siempre exista y sea lista
        if 'headers' not in catalog or not isinstance(catalog['headers'], list):
            catalog['headers'] = []
        # Refuerzo: asegurar que rows siempre exista y sea lista
        if ('rows' not in catalog or catalog['rows'] is None) and ('data' in catalog and isinstance(catalog['data'], list)):
            catalog['rows'] = catalog['data']
        elif 'rows' not in catalog or catalog['rows'] is None:
            catalog['rows'] = []
        # Añadir información sobre la colección de origen
        catalog['collection_source'] = collection_source
        catalog['_id_str'] = str(catalog['_id'])
        
        # Añadir información adicional al catálogo
        if "created_at" in catalog and catalog["created_at"]:
            if isinstance(catalog['created_at'], str):
                catalog["created_at_formatted"] = catalog['created_at']
            else:
                catalog["created_at_formatted"] = catalog["created_at"].strftime("%d/%m/%Y %H:%M")
        else:
            catalog["created_at_formatted"] = "Fecha desconocida"
        
        # Contar filas según la estructura
        if 'rows' in catalog and catalog['rows'] is not None:
            catalog['row_count'] = len(catalog['rows'])
            # Para compatibilidad con la plantilla
            catalog['data'] = catalog['rows']
        elif 'data' in catalog and catalog['data'] is not None:
            catalog['row_count'] = len(catalog['data'])
        else:
            catalog['row_count'] = 0
            catalog['data'] = []
            
        # Procesar las imágenes en cada fila
        from app.utils.image_utils import get_image_url
        from app.utils.s3_utils import get_s3_url
        
        # Verificar si hay datos en el catálogo
        if 'data' in catalog and catalog['data']:
            for row in catalog['data']:
                # Procesar imágenes en el campo 'imagenes'
                if 'imagenes' in row and row['imagenes']:
                    # Crear un array con las URLs de las imágenes
                    row['imagen_urls'] = []
                    for img in row['imagenes']:
                        if img and len(img) > 5:  # Verificar que el nombre de la imagen es válido
                            # Intentar obtener la URL de S3 primero
                            s3_url = get_s3_url(img)
                            if s3_url:
                                row['imagen_urls'].append(s3_url)
                                logger.debug(f"[ADMIN] Imagen S3 encontrada: {img} -> {s3_url}")
                            else:
                                # Si no está en S3, usar la URL local
                                local_url = url_for('static', filename=f'uploads/{img}')
                                row['imagen_urls'].append(local_url)
                                logger.debug(f"[ADMIN] Usando URL local para imagen: {img} -> {local_url}")
                
                # Procesar imágenes en el campo 'images' (compatibilidad)
                elif 'images' in row and row['images']:
                    # Crear un array con las URLs de las imágenes
                    row['imagen_urls'] = []
                    for img in row['images']:
                        if img and len(img) > 5:  # Verificar que el nombre de la imagen es válido
                            # Intentar obtener la URL de S3 primero
                            s3_url = get_s3_url(img)
                            if s3_url:
                                row['imagen_urls'].append(s3_url)
                                logger.debug(f"[ADMIN] Imagen S3 encontrada: {img} -> {s3_url}")
                            else:
                                # Si no está en S3, usar la URL local
                                local_url = url_for('static', filename=f'uploads/{img}')
                                row['imagen_urls'].append(local_url)
                                logger.debug(f"[ADMIN] Usando URL local para imagen: {img} -> {local_url}")
                    
                    # Para compatibilidad, copiar a 'imagenes'
                    row['imagenes'] = row['images']
                
            logger.info(f"[ADMIN] Procesadas {catalog['row_count']} filas con imágenes para el catálogo {catalog_id}")
        else:
            logger.warning(f"[ADMIN] El catálogo {catalog_id} no tiene filas o datos")

        
        logger.info(f"[ADMIN] Mostrando catálogo desde {collection_source}: {catalog.get('name', 'Sin nombre')}")
        # Determinar return_url
        return_url = request.referrer
        # Intentar deducir el user_id para volver a la lista de catálogos del usuario
        user_id = None
        if 'created_by_id' in catalog and catalog['created_by_id']:
            user_id = str(catalog['created_by_id'])
        elif 'created_by' in catalog and catalog['created_by']:
            user = db.users.find_one({"$or": [{"email": catalog['created_by']}, {"username": catalog['created_by']}]})
            if user:
                user_id = str(user['_id'])
        if not return_url and user_id:
            return_url = url_for('admin.ver_catalogos_usuario_por_id', user_id=user_id)
        elif not return_url:
            return_url = url_for('admin.dashboard_admin')
        return render_template("admin/ver_catalogo.html", catalog=catalog, error=None, collection_source=collection_source, return_url=return_url)
    except Exception as e:
        logger.error(f"Error en ver_catalogo_unificado: {str(e)}", exc_info=True)
        flash(f"Error al cargar el catálogo: {str(e)}", "error")
        return redirect(url_for('admin.dashboard_admin'))

@admin_bp.route("/catalogo/<collection_source>/<catalog_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_catalogo_admin(collection_source, catalog_id):
    logger.info(f"[ADMIN] Entrando en editar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}")
    try:
        db = get_db()
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        if not catalog:
            logger.warning(f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}")
            flash("Catálogo no encontrado", "warning")
            return redirect(url_for("admin.dashboard_admin"))
            
        # Añadir información sobre la colección de origen
        catalog['collection_source'] = collection_source
        catalog['_id_str'] = str(catalog['_id'])
        
        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description", "")
            headers_raw = request.form.get("headers")
            update_data = {
                "name": name,
                "description": description,
                "updated_at": datetime.utcnow()
            }
            if headers_raw is not None:
                headers = [h.strip() for h in headers_raw.split(",") if h.strip()]
                update_data["headers"] = headers
            # Actualizar el catálogo en la colección correspondiente
            collection.update_one(
                {"_id": ObjectId(catalog_id)}, 
                {"$set": update_data}
            )
            flash("Catálogo actualizado correctamente", "success")
            # Intentar obtener el ID del usuario para redirigir
            user_id = None
            if 'created_by_id' in catalog and catalog['created_by_id']:
                user_id = str(catalog['created_by_id'])
            elif 'created_by' in catalog and catalog['created_by']:
                # Buscar el usuario por email o username
                user = db.users.find_one({"$or": [{"email": catalog['created_by']}, {"username": catalog['created_by']}]})
                if user:
                    user_id = str(user['_id'])
            if user_id:
                return redirect(url_for("admin.ver_catalogos_usuario_por_id", user_id=user_id))
            else:
                return redirect(url_for("admin.dashboard_admin"))
                
        return render_template("admin/editar_catalogo.html", catalog=catalog, collection_source=collection_source)
    except Exception as e:
        logger.error(f"Error en editar_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al editar el catálogo: {str(e)}", "error")
        return redirect(url_for('admin.dashboard_admin'))

@admin_bp.route("/catalogo/<collection_source>/<catalog_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_catalogo_admin(collection_source, catalog_id):
    try:
        logger.info(f"[ADMIN] Entrando en eliminar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}")
        
        db = get_db()
        collection = db[collection_source]
        catalog = collection.find_one({"_id": ObjectId(catalog_id)})
        
        if not catalog:
            logger.warning(f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}")
            flash("Catálogo no encontrado", "warning")
            return redirect(url_for("admin.dashboard_admin"))
            
        # Eliminar el catálogo de la colección correspondiente
        result = collection.delete_one({"_id": ObjectId(catalog_id)})
        
        if result.deleted_count > 0:
            logger.info(f"[ADMIN] Catálogo eliminado correctamente: {catalog_id} de {collection_source}")
            flash("Catálogo eliminado correctamente", "success")
        else:
            logger.warning(f"[ADMIN] No se pudo eliminar el catálogo: {catalog_id} de {collection_source}")
            flash("No se pudo eliminar el catálogo", "warning")
            
        # Redirigir a la página anterior o al dashboard
        return redirect(request.referrer or url_for("admin.dashboard_admin"))
    except Exception as e:
        logger.error(f"Error en eliminar_catalogo_admin: {str(e)}", exc_info=True)
        flash(f"Error al eliminar el catálogo: {str(e)}", "error")
        return redirect(url_for('admin.dashboard_admin'))

@admin_bp.route("/db-scripts", methods=["GET", "POST"])
@admin_required
def db_scripts():
    """
    Maneja la ejecución de scripts de base de datos desde la interfaz de administración.
    
    Permite ejecutar scripts de mantenimiento de la base de datos con argumentos opcionales.
    Incluye medidas de seguridad para prevenir ejecución de comandos maliciosos.
    """
    import glob
    import shlex
    import time
    import subprocess
    from datetime import datetime
    
    # Configuración de directorios
    scripts_dir = os.path.join(os.getcwd(), "tools", "db_utils")
    
    # Lista de scripts permitidos (solo .py y que no empiecen con _)
    blacklist = {"__init__.py", "google_drive_utils.py"}
    scripts = []
    
    # Obtener información detallada de cada script
    for script_path in glob.glob(os.path.join(scripts_dir, "*.py")):
        script_name = os.path.basename(script_path)
        if script_name.startswith("_") or script_name in blacklist:
            continue
            
        # Obtener descripción del script (primera línea de comentario)
        description = "Sin descripción"
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') and 'descripci' in line.lower():
                        description = line.lstrip('#').strip()
                        break
        except Exception as e:
            description = f"Error al leer descripción: {str(e)}"
            
        scripts.append({
            'name': script_name,
            'path': script_path,
            'description': description,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(script_path)).strftime('%Y-%m-%d %H:%M')
        })
    
    # Ordenar scripts por nombre
    scripts = sorted(scripts, key=lambda x: x['name'])
    
    # Variables para el formulario
    result = None
    error = None
    selected_script = None
    args = ""
    duration = None
    
    # Procesar envío del formulario
    if request.method == "POST":
        selected_script = request.form.get("script")
        args = request.form.get("args", "").strip()
        
        # Validar script seleccionado
        if not selected_script or not selected_script.endswith(".py"):
            error = "Script no válido."
        else:
            # Verificar que el script esté en la lista permitida
            script_info = next((s for s in scripts if s['name'] == selected_script), None)
            if not script_info:
                error = "Script no permitido."
            else:
                # Construir comando de forma segura
                cmd = ["python3", script_info['path']]
                
                # Validar y añadir argumentos
                if args:
                    try:
                        # Validar argumentos (solo permitir ciertos caracteres)
                        if not all(c.isalnum() or c in ' -_=.' for c in args):
                            raise ValueError("Caracteres no permitidos en los argumentos")
                            
                        # Añadir argumentos de forma segura
                        cmd.extend(shlex.split(args))
                    except Exception as e:
                        error = f"Error en los argumentos: {str(e)}"
                
                # Ejecutar el script
                if not error:
                    start_time = time.time()
                    try:
                        # Ejecutar con timeout de 5 minutos
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=scripts_dir  # Ejecutar desde el directorio del script
                        )
                        
                        try:
                            out, err = proc.communicate(timeout=300)  # 5 minutos de timeout
                            duration = round(time.time() - start_time, 2)
                            result = out
                            error = err if err and err.strip() else None
                            
                            # Registrar en log de auditoría
                            audit_log(
                                f"Ejecución de script DB: {selected_script} "
                                f"args: {args} duración: {duration}s"
                            )
                            
                            # Añadir mensaje de éxito
                            flash(f"Script ejecutado correctamente en {duration} segundos.", "success")
                            
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            error = "El script excedió el tiempo máximo de ejecución (5 minutos)"
                            
                    except Exception as e:
                        error = f"Error al ejecutar el script: {str(e)}"
    
    # Mensaje de advertencia de seguridad
    warning = (
        "⚠️ ADVERTENCIA: La ejecución de scripts puede afectar la base de datos. "
        "Asegúrate de entender lo que hace el script antes de ejecutarlo. "
        "Se recomienda probar en un entorno de desarrollo primero."
    )
    
    return render_template(
        "admin/db_scripts.html",
        scripts=scripts,
        result=result,
        error=error,
        selected_script=selected_script,
        args=args,
        duration=duration,
        warning=warning
    )

@admin_bp.route('/db-status')
@admin_required
def db_status():
    """Muestra el estado de la conexión a MongoDB"""
    client = get_mongo_client()
    status = {
        'is_connected': False,
        'error': None,
        'databases': [],
        'collections': [],
        'server_info': None,
        'server_status': {}
    }
    
    try:
        # Probar conexión
        client.admin.command('ping')
        status['is_connected'] = True
        
        # Obtener información de la base de datos
        status['databases'] = client.list_database_names()
        
        # Obtener colecciones de la base de datos actual
        db = get_mongo_db()
        if db is not None:
            try:
                status['collections'] = db.list_collection_names()
            except Exception as e:
                current_app.logger.error(f"Error al obtener colecciones: {str(e)}")
                status['collections'] = []
                status['error'] = f"Error al obtener colecciones: {str(e)}"
        
        # Obtener información del servidor y convertir objetos no serializables
        def convert_timestamps(obj):
            from bson import Timestamp
            from bson.objectid import ObjectId
            from datetime import datetime
            
            if isinstance(obj, (list, tuple)):
                return [convert_timestamps(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, Timestamp):
                return {
                    'timestamp': obj.time,
                    'increment': obj.inc,
                    'as_datetime': datetime.fromtimestamp(obj.time).isoformat(),
                    '_type': 'Timestamp'
                }
            elif isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, bytes):
                # Convertir bytes a string si es posible, o a una representación en base64
                try:
                    return obj.decode('utf-8')
                except UnicodeDecodeError:
                    import base64
                    return {
                        '_type': 'bytes',
                        'base64': base64.b64encode(obj).decode('ascii'),
                        'length': len(obj)
                    }
            elif hasattr(obj, 'isoformat'):  # Para objetos datetime
                return obj.isoformat()
            elif hasattr(obj, 'items'):  # Para objetos tipo dict
                return {str(k): convert_timestamps(v) for k, v in obj.items()}
            elif hasattr(obj, '__dict__'):  # Para objetos con __dict__
                return convert_timestamps(obj.__dict__)
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                # Para cualquier otro tipo, devolver su representación como string
                return str(obj)
        
        # Obtener y procesar la información del servidor
        server_info = client.server_info()
        status['server_info'] = convert_timestamps(server_info)
        
        # Obtener y procesar estadísticas del servidor
        try:
            server_status = client.admin.command('serverStatus')
            status['server_status'] = convert_timestamps(server_status)
        except Exception as e:
            status['server_status'] = {'error': f'No se pudo obtener el estado del servidor: {str(e)}'}
            
    except Exception as e:
        status['error'] = f"Error al conectar con MongoDB: {str(e)}"
        current_app.logger.error(f"Error en db_status: {str(e)}\n{traceback.format_exc()}")
    return render_template("admin/db_status.html", status=status)

@admin_bp.route('/db/monitor')
@admin_required
def db_monitor():
    """Página de monitoreo en tiempo real de la base de datos"""
    client = get_mongo_client()
    status = {'is_connected': False, 'error': None, 'stats': {}, 'server_status': {}}
    
    try:
        # Verificar conexión
        client.admin.command('ping')
        status['is_connected'] = True
        
        # Obtener estadísticas básicas
        db = get_mongo_db()
        if db is not None:
            try:
                status['stats'] = db.command('dbstats')
            except Exception as e:
                current_app.logger.error(f"Error al obtener estadísticas de la base de datos: {str(e)}")
                status['error'] = f"Error al obtener estadísticas: {str(e)}"
        
        # Obtener estado del servidor
        server_status = client.admin.command('serverStatus')
        status['server_status'] = server_status
        
        # Inicializar contadores de operaciones si no existen
        if 'opcounters' not in session:
            session['opcounters'] = {
                'query': 0,
                'insert': 0,
                'update': 0,
                'delete': 0,
                'getmore': 0,
                'command': 0
            }
        
        # Guardar timestamp de la última actualización
        session['last_update'] = time.time()
        
        # Obtener operaciones lentas (últimas 10)
        try:
            current_ops = client.admin.command('currentOp')
            if current_ops and 'inprog' in current_ops:
                slow_ops = [
                    op for op in current_ops['inprog'] 
                    if op.get('secs_running', 0) > 1 and 
                    (op.get('op') in ['query', 'insert', 'update', 'remove'] or 'findAndModify' in str(op.get('command', {})))
                ]
                status['slow_ops'] = slow_ops[:10]
            else:
                status['slow_ops'] = []
        except Exception as e:
            current_app.logger.error(f"Error al obtener operaciones lentas: {str(e)}")
            status['slow_ops'] = []
        
    except Exception as e:
        status['error'] = f"Error al obtener estadísticas: {str(e)}"
        current_app.logger.error(f"Error en db_monitor: {str(e)}\n{traceback.format_exc()}")
    
    return render_template("admin/db_monitor.html", status=status)

# Variables globales para el seguimiento de operaciones
last_ops = {}
last_update = time.time()

@admin_bp.route('/api/db/ops')
@admin_required
def get_db_ops():
    """
    Endpoint para obtener estadísticas de operaciones en tiempo real.
    Usa variables globales para el seguimiento entre solicitudes.
    """
    global last_ops, last_update
    
    try:
        client = get_mongo_client()
        server_status = client.admin.command('serverStatus')
        
        # Obtener contadores actuales
        current_ops = server_status.get('opcounters', {})
        current_time = time.time()
        
        # Calcular operaciones por segundo
        time_diff = current_time - last_update
        ops_per_sec = {}
        
        if last_ops and time_diff > 0:
            for op_type in ['query', 'insert', 'update', 'delete', 'getmore', 'command']:
                if op_type in current_ops and op_type in last_ops:
                    ops_diff = current_ops[op_type] - last_ops[op_type]
                    ops_per_sec[op_type] = round(ops_diff / time_diff, 2)
        
        # Actualizar estado para la próxima solicitud
        last_ops = current_ops
        last_update = current_time
        
        # Obtener información de memoria
        memory = server_status.get('mem', {})
        
        # Obtener información de conexiones
        connections = server_status.get('connections', {})
        
        # Obtener operaciones lentas
        current_op = client.admin.current_op()
        slow_ops = []
        if 'inprog' in current_op:
            for op in current_op['inprog']:
                if 'secs_running' in op and op['secs_running'] > 1:  # Operaciones que llevan más de 1 segundo
                    slow_ops.append({
                        'opid': op.get('opid'),
                        'secs_running': op.get('secs_running'),
                        'op': op.get('op'),
                        'ns': op.get('ns'),
                        'client': op.get('client')
                    })
        
        return jsonify({
            'success': True,
            'ops_per_sec': ops_per_sec,
            'memory': memory,
            'connections': connections,
            'slow_ops': slow_ops[:10],  # Devolver solo las 10 operaciones más lentas
            'timestamp': current_time
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en get_db_ops: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def get_backup_dir():
    """Obtiene el directorio de respaldos, asegurando que exista"""
    backup_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'backups'))
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

@admin_bp.route('/db/backup', methods=['GET', 'POST'])
@admin_required
def db_backup():
    """Maneja la creación y gestión de respaldos"""
    try:
        backup_dir = get_backup_dir()
        
        # Verificar permisos de escritura
        if not os.access(backup_dir, os.W_OK):
            raise Exception(f"No se tienen permisos de escritura en {backup_dir}")
            
        # Verificar espacio en disco (mínimo 1GB libre)
        disk_usage = shutil.disk_usage(backup_dir)
        if disk_usage.free < 1024**3:  # 1GB
            raise Exception("Espacio en disco insuficiente (se requiere al menos 1GB libre)")
        
        if request.method == 'POST':
            try:
                # Generar nombre de archivo con timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(backup_dir, f'mongodb_backup_{timestamp}.gz')
                
                # Ejecutar mongodump
                mongo_uri = current_app.config['MONGO_URI']
                cmd = [
                    'mongodump',
                    f'--uri={mongo_uri}',
                    '--gzip',
                    f'--archive={backup_file}'
                ]
                
                current_app.logger.info(f"Ejecutando comando de respaldo: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"Error en mongodump: {result.stderr}"
                    current_app.logger.error(error_msg)
                    return jsonify({
                        'status': 'error',
                        'message': error_msg
                    }), 500
                
                # Verificar que el archivo se creó correctamente
                if not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
                    error_msg = "El archivo de respaldo no se creó correctamente"
                    current_app.logger.error(error_msg)
                    return jsonify({
                        'status': 'error',
                        'message': error_msg
                    }), 500
                
                audit_log(f"Respaldo creado: {os.path.basename(backup_file)}")
                # Limpiar respaldos antiguos (mantener los 5 más recientes)
                try:
                    backups = sorted(
                        [f for f in os.listdir(backup_dir) 
                         if f.startswith('mongodb_backup_') and f.endswith('.gz')],
                        reverse=True
                    )
                    for old_backup in backups[5:]:
                        try:
                            os.remove(os.path.join(backup_dir, old_backup))
                            current_app.logger.info(f"Respaldo antiguo eliminado: {old_backup}")
                        except Exception as e:
                            current_app.logger.error(f"Error al eliminar respaldo {old_backup}: {str(e)}")
                except Exception as e:
                    current_app.logger.error(f"Error al limpiar respaldos antiguos: {str(e)}")
                    # No fallar la operación principal si falla la limpieza
                # Devolver JSON con URL de descarga
                download_url = url_for('admin.download_backup', filename=os.path.basename(backup_file))
                return jsonify({
                    'status': 'success',
                    'download_url': download_url
                })
            except Exception as e:
                current_app.logger.error(f"Error al crear respaldo: {str(e)}\n{traceback.format_exc()}")
                # Intentar eliminar el archivo parcial si existe
                if 'backup_file' in locals() and os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except:
                        pass
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            # No continuar con render_template después de POST
            # (el frontend espera solo JSON)
            
        
        # Función auxiliar para obtener información de archivos
        def get_file_info(filepath):
            from collections import namedtuple
            FileInfo = namedtuple('FileInfo', ['exists', 'size', 'mtime'])
            
            try:
                if not os.path.exists(filepath):
                    return FileInfo(False, 0, None)
                    
                stat = os.stat(filepath)
                return FileInfo(
                    exists=True,
                    size=stat.st_size,
                    mtime=datetime.fromtimestamp(stat.st_mtime)
                )
            except Exception as e:
                current_app.logger.error(f"Error al obtener info de archivo {filepath}: {str(e)}")
                return FileInfo(False, 0, None)
        
        # Listar respaldos existentes
        backups = []
        try:
            if os.path.exists(backup_dir):
                backups = sorted(
                    [f for f in os.listdir(backup_dir) 
                     if f.startswith('mongodb_backup_') and f.endswith('.gz')],
                    reverse=True
                )
        except Exception as e:
            current_app.logger.error(f"Error al listar respaldos: {str(e)}")
            flash('Error al listar los respaldos existentes', 'error')
        
        # Obtener el conteo de respaldos en Google Drive
        drive_backups_count = 0
        try:
            db = get_db()
            drive_backups_count = db.backups.count_documents({})
        except Exception as e:
            current_app.logger.error(f"Error al contar respaldos en Drive: {str(e)}")
            # No mostramos error al usuario para no interrumpir la funcionalidad principal
        
        # Solo renderizar plantilla en GET
        return render_template(
            'admin/db_backup.html',
            backups=backups,
            backup_dir=backup_dir,
            get_file_info=get_file_info,
            drive_backups_count=drive_backups_count
        )
        
    except Exception as e:
        current_app.logger.error(f"Error en db_backup: {str(e)}\n{traceback.format_exc()}")
        flash(f'Error en la operación de respaldo: {str(e)}', 'error')
        return render_template('admin/db_backup.html', backups=[])

@admin_bp.route('/db/performance', methods=['GET', 'POST'])
@admin_required
def db_performance():
    """Ejecuta y muestra pruebas de rendimiento"""
    results = None
    
    if request.method == 'POST':
        try:
            # Obtener parámetros del formulario
            num_ops = int(request.form.get('num_ops', 100))
            batch_size = int(request.form.get('batch_size', 10))
            
            # Ejecutar pruebas de rendimiento
            db = get_mongo_db()
            test_collection = db.performance_test
            
            # Limpiar colección de prueba
            test_collection.drop()
            
            # Prueba de inserción
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                batch = [{'value': j, 'timestamp': datetime.utcnow()} 
                        for j in range(i, min(i + batch_size, num_ops))]
                test_collection.insert_many(batch)
            insert_time = time.time() - start_time
            
            # Prueba de consulta
            start_time = time.time()
            for _ in range(num_ops):
                list(test_collection.find().limit(10))
            query_time = time.time() - start_time
            
            # Prueba de actualización
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                test_collection.update_many(
                    {'_id': {'$in': [doc['_id'] for doc in test_collection.find().skip(i).limit(batch_size)]}},
                    {'$set': {'updated': True}}
                )
            update_time = time.time() - start_time
            
            # Limpiar
            test_collection.drop()
            
            # Crear métricas con los resultados
            insert_metrics = {
                'time': insert_time,
                'ops_sec': num_ops / insert_time if insert_time > 0 else 0
            }
            query_metrics = {
                'time': query_time,
                'ops_sec': num_ops / query_time if query_time > 0 else 0
            }
            update_metrics = {
                'time': update_time,
                'ops_sec': num_ops / update_time if update_time > 0 else 0
            }
            
            # Estructurar los resultados según lo esperado por la plantilla
            results = {
                'status': 'success',
                'operations': num_ops,
                'batch_size': batch_size,
                'metrics': {
                    'insert': insert_metrics,
                    'query': query_metrics,
                    'update': update_metrics
                },
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            results = {
                'status': 'error',
                'message': f'Error al ejecutar pruebas: {str(e)}',
                'traceback': traceback.format_exc()
            }
            current_app.logger.error(f"Error en db_performance: {str(e)}\n{results['traceback']}")
    
    return render_template('admin/db_performance.html', results=results)

# Definir el blueprint con el prefijo de URL correcto
# Cambiamos el nombre a 'admin' para que coincida con el prefijo
admin_logs_bp = Blueprint('admin_logs', __name__)

# Decorador para restringir acceso solo a admin (importamos el decorador principal)
from app.decorators import admin_required as admin_required_logs

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/flask_debug.log'))

@admin_logs_bp.route('/logs')
@admin_required_logs
def logs_manual():
    return render_template('admin/logs_manual.html')

@admin_logs_bp.route('/logs/tail')
@admin_required_logs
def logs_tail():
    import os
    from datetime import datetime
    
    # Obtener parámetros
    n = int(request.args.get('n', 20))
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    log_file = request.args.get('log_file', 'flask_debug.log')
    
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_path = os.path.join(logs_dir, log_file)
    
    if not os.path.isfile(log_path):
        return jsonify({'logs': [f'Archivo no encontrado: {log_file}\n'], 'error': 'Archivo no encontrado'}), 404
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Si se especifican fechas, filtrar por rango
        if date_from or date_to:
            filtered_lines = []
            date_format = '%Y-%m-%d'
            
            if date_from:
                date_from = datetime.strptime(date_from, date_format).date()
            if date_to:
                date_to = datetime.strptime(date_to, date_format).date()
            
            for line in lines:
                # Extraer la fecha del log (asumiendo formato de fecha al inicio de la línea)
                log_date_str = ' '.join(line.split()[:2])  # Toma los dos primeros segmentos (fecha y hora)
                try:
                    log_datetime = datetime.strptime(log_date_str, '%Y-%m-%d %H:%M:%S,%f')
                    log_date = log_datetime.date()
                    
                    # Aplicar filtros de fecha
                    if date_from and log_date < date_from:
                        continue
                    if date_to and log_date > date_to:
                        continue
                        
                    filtered_lines.append(line)
                except ValueError:
                    # Si no se puede extraer la fecha, incluir la línea por defecto
                    filtered_lines.append(line)
            
            # Aplicar límite de líneas si se especificó
            result_lines = filtered_lines[-n:] if n > 0 else filtered_lines
        else:
            # Si no hay filtro de fechas, simplemente tomar las últimas N líneas
            result_lines = lines[-n:] if n > 0 else lines
            
        return jsonify({
            'logs': result_lines,
            'total_lines': len(lines),
            'filtered_lines': len(result_lines)
        })
        
    except Exception as e:
        return jsonify({
            'logs': [f'Error al leer el archivo de log: {str(e)}\n'],
            'error': str(e)
        }), 500

@admin_logs_bp.route('/logs/search')
@admin_required_logs
def logs_search():
    import os
    kw = request.args.get('kw', '').strip()
    log_file = request.args.get('log_file', 'flask_debug.log')
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        from flask import abort
        abort(404, description=f'Archivo no encontrado: {log_file}')
    if not kw:
        return jsonify({'logs': []})  # Esto es éxito, no error, se mantiene igual.
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l for l in f if kw.lower() in l.lower()]
    return jsonify({'logs': lines})

@admin_logs_bp.route('/logs/download')
@admin_required_logs
def logs_download():
    import os
    log_file = request.args.get('log_file', 'flask_debug.log')
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return 'Archivo no encontrado', 404
    return send_file(log_path, as_attachment=True, download_name=log_file)

@admin_logs_bp.route('/logs/clear', methods=['POST'])
@admin_required_logs
def logs_clear():
    import os
    log_file = request.args.get('log_file', 'flask_debug.log')
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return jsonify({'status': f'Archivo no encontrado: {log_file}'}), 404
    with open(log_path, 'w') as f:
        f.truncate(0)
    return jsonify({'status': f'Log {log_file} limpiado correctamente'})

@admin_logs_bp.route('/logs/size')
@admin_required_logs
def logs_size():
    import os
    log_file = request.args.get('log_file', 'flask_debug.log')
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return jsonify({'size': 0, 'backups': 0, 'error': 'Archivo no encontrado'}), 404
    size = os.path.getsize(log_path)
    backups = len([f for f in os.listdir(logs_dir) if f.startswith(log_file + '.')])
    return jsonify({'size': size, 'backups': backups})

@admin_bp.route("/backups/list", methods=["GET", "POST"])
@admin_required
def backups_list():
    backups_dir = os.path.join(os.getcwd(), "backups")
    backup_files = get_backup_files(backups_dir)
    if request.method == "POST":
        # Borrado individual
        filename = request.form.get("filename")
        if filename and '..' not in filename and '/' not in filename:
            file_path = os.path.join(backups_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    flash(f"Backup {filename} eliminado correctamente", "success")
                    audit_log(f"Backup eliminado manualmente por {session.get('user_id', session.get('username', 'desconocido'))} - {filename}")
                except Exception as e:
                    flash(f"Error al eliminar el backup: {str(e)}", "danger")
            else:
                flash("El archivo no existe", "warning")
        else:
            flash("Nombre de archivo no válido", "danger")
        return redirect(url_for("admin.backups_list"))
    return render_template("admin/backups_list.html", backup_files=backup_files)

@admin_bp.route("/backups/download/<filename>")
@admin_required
def download_backup(filename):
    backups_dir = os.path.join(os.getcwd(), "backups")
    if '..' in filename or '/' in filename:
        flash("Nombre de archivo no válido", "danger")
        return redirect(url_for("admin.backups_list"))
    file_path = os.path.join(backups_dir, filename)
    if not os.path.exists(file_path):
        flash("El archivo no existe", "warning")
        return redirect(url_for("admin.backups_list"))
    audit_log(f"Descarga de backup por {session.get('user_id', session.get('username', 'desconocido'))} - {filename}")
    return send_file(file_path, as_attachment=True, download_name=filename)

@admin_bp.route("/reset_gdrive_token", methods=["POST"])
@admin_required
def reset_gdrive_token_route():
    import subprocess
    import sys
    try:
        script_path = os.path.join(os.path.dirname(__file__), '../../tools/db_utils/google_drive_utils.py')
        result = subprocess.run([sys.executable, script_path, '--reset-token'], capture_output=True, text=True)
        if result.returncode == 0:
            flash("Token de Google Drive eliminado correctamente. Sigue las instrucciones para regenerar el refresh_token.", "success")
            flash(result.stdout, "info")
        else:
            flash(f"Error al eliminar el token: {result.stderr}", "danger")
    except Exception as e:
        flash(f"Error al ejecutar el reseteo de token: {str(e)}", "danger")
    return redirect(url_for('maintenance.maintenance_dashboard'))

@admin_bp.route("/gdrive_upload_test", methods=["GET", "POST"])
@admin_required
def gdrive_upload_test():
    import os
    from werkzeug.utils import secure_filename
    from tools.db_utils.google_drive_utils import upload_to_drive
    uploaded_links = []
    if request.method == "POST":
        files = request.files.getlist("test_files")
        if not files or files[0].filename == '':
            flash("No se seleccionó ningún archivo.", "warning")
            return redirect(url_for('admin.gdrive_upload_test'))
        for file in files:
            filename = secure_filename(file.filename)
            temp_path = os.path.join("/tmp", filename)
            file.save(temp_path)
            try:
                result = upload_to_drive(temp_path)
                if result.get('success'):
                    # Extraer solo la URL del resultado
                    file_url = result.get('file_url', '#')
                    uploaded_links.append((filename, file_url))
                else:
                    # Si hay error, mostramos el mensaje de error
                    error_msg = result.get('error', 'Error desconocido')
                    flash(f"Error al subir '{filename}': {error_msg}", "danger")
                flash(f"Archivo '{filename}' subido correctamente a Google Drive.", "success")
            except Exception as e:
                flash(f"Error al subir '{filename}': {str(e)}", "danger")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    return render_template("admin/gdrive_upload_test.html", uploaded_links=uploaded_links)

@admin_bp.route("/backup/upload-to-drive/<filename>", methods=["POST"])
@admin_required
def upload_backup_to_drive(filename):
    """
    Sube un archivo de respaldo a Google Drive y lo elimina localmente si tiene éxito.
    
    Args:
        filename (str): Nombre del archivo de respaldo a subir
        
    Returns:
        JSON: Respuesta con el resultado de la operación
    """
    import os
    from flask import jsonify, current_app
    from werkzeug.utils import secure_filename
    from tools.db_utils.google_drive_utils import upload_to_drive
    
    try:
        # Validar el nombre del archivo
        if '..' in filename or '/' in filename:
            current_app.logger.warning(f"Intento de acceso a ruta no permitida: {filename}")
            return jsonify({
                'success': False,
                'error': 'Nombre de archivo no válido',
                'message': 'El nombre del archivo contiene caracteres no permitidos.'
            }), 400
            
        # Construir la ruta completa del archivo usando la función get_backup_dir()
        backup_dir = get_backup_dir()
        file_path = os.path.join(backup_dir, secure_filename(filename))
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            current_app.logger.warning(f"Archivo no encontrado: {file_path}")
            return jsonify({
                'success': False,
                'status': 'error',
                'error': 'Archivo no encontrado',
                'message': f'El archivo {filename} no existe en el servidor.'
            }), 404
            
        # Obtener información del archivo local
        file_size = os.path.getsize(file_path)
        file_info = {
            'filename': filename,
            'file_size': file_size,
            'local_path': file_path,
            'last_modified': os.path.getmtime(file_path)
        }
        
        current_app.logger.info(f"Iniciando subida a Google Drive: {file_info}")
        
        # Subir a Google Drive
        result = upload_to_drive(file_path)
        
        if result.get('success'):
            # Obtener la URL de descarga directa
            file_id = result.get('file_id')
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            web_view_url = result.get('file_url')  # Usar la URL de vista web que ya viene de upload_to_drive
            
            # Guardar metadatos en la base de datos
            backup_metadata = {
                'filename': filename,
                'file_id': file_id,
                'file_size': file_size,
                'download_url': download_url,
                'web_view_url': web_view_url,
                'uploaded_at': datetime.utcnow(),
                'uploaded_by': current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None,
                'status': 'uploaded',
                'folder_name': result.get('folder_name', 'Backups_CatalogoTablas')
            }
            
            # Insertar en la colección de respaldos
            db = get_db()
            db.backups.insert_one(backup_metadata)
            
            # Eliminar el archivo local si la subida fue exitosa
            try:
                os.remove(file_path)
                current_app.logger.info(f"Archivo {filename} eliminado localmente después de subir a Google Drive")
                
                # Registrar la acción en el log de auditoría
                log_action(
                    action='backup_uploaded_to_drive',
                    message=f'Backup subido a Google Drive: {filename} ({file_size/1024/1024:.2f} MB)',
                    details={
                        'file_id': file_id,
                        'file_name': filename,
                        'file_size': file_size,
                        'drive_folder': result.get('folder_name', 'Backups_CatalogoTablas'),
                        'download_url': download_url,
                        'web_view_url': web_view_url
                    },
                    user_id=current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None,
                    collection='backups'
                )
                
                # Preparar respuesta exitosa
                response_data = {
                    'success': True,
                    'message': 'El respaldo se ha subido correctamente a Google Drive y se ha eliminado localmente.',
                    'file_info': {
                        'filename': filename,
                        'file_id': file_id,
                        'file_size': file_size,
                        'file_size_mb': round(file_size / (1024 * 1024), 2),
                        'download_url': download_url,
                        'web_view_url': web_view_url,
                        'uploaded_at': backup_metadata['uploaded_at'].isoformat(),
                        'folder_name': result.get('folder_name', 'Backups_CatalogoTablas')
                    }
                }
                
                current_app.logger.info(f"Subida a Google Drive completada: {response_data}")
                return jsonify(response_data)
                
            except Exception as e:
                error_msg = f"Error al eliminar el archivo local {filename}: {str(e)}"
                current_app.logger.error(error_msg, exc_info=True)
                
                # Registrar el error en el log de auditoría
                log_action(
                    action='backup_upload_error',
                    message=f'Error al eliminar archivo local después de subir a Google Drive: {filename}',
                    details={
                        'error': str(e),
                        'file_name': filename,
                        'file_size': file_size,
                        'drive_folder': result.get('folder_name', 'Backups_CatalogoTablas')
                    },
                    user_id=current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None,
                    collection='backups'
                )
                
                # Si falla la eliminación local, la subida a Drive fue exitosa, así que lo consideramos un éxito parcial
                return jsonify({
                    'success': True,
                    'warning': 'El archivo se subió a Google Drive pero no se pudo eliminar localmente.',
                    'error': error_msg,
                    'file_info': {
                        'filename': result.get('filename'),
                        'file_id': result.get('file_id'),
                        'download_url': result.get('download_url'),
                        'web_view_url': result.get('web_view_url'),
                        'folder_name': result.get('folder_name')
                    }
                }), 207  # Código 207 Multi-Status para éxito parcial
                
        else:
            error_msg = f"Error al subir a Google Drive: {result.get('error')}"
            current_app.logger.error(error_msg)
            
            # Registrar el error en el log de auditoría
            log_action(
                action='backup_upload_failed',
                message=f'Error al subir archivo a Google Drive: {filename}',
                details={
                    'error': result.get('error', 'Error desconocido'),
                    'file_name': filename,
                    'file_size': file_size
                },
                user_id=current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None,
                collection='backups'
            )
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Error desconocido'),
                'message': 'El archivo no se pudo subir a Google Drive. Por favor, inténtalo de nuevo.'
            }), 500
            
    except Exception as e:
        error_msg = f"Error inesperado en upload_backup_to_drive: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        
        # Registrar el error inesperado en el log de auditoría
        log_action(
            action='backup_upload_error',
            message=f'Error inesperado al subir archivo a Google Drive: {filename}',
            details={
                'error': str(e),
                'file_name': filename,
                'traceback': traceback.format_exc()
            },
            user_id=current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None,
            collection='backups'
        )
        
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'message': 'Ocurrió un error inesperado al procesar la solicitud.',
            'details': str(e) if current_app.config.get('DEBUG') else None
        }), 500

@admin_bp.route("/drive-backups")
@admin_required
def list_drive_backups():
    """
    Muestra una lista de todos los respaldos almacenados en Google Drive.
    """
    try:
        db = get_db()
        # Obtener todos los respaldos ordenados por fecha de subida descendente
        backups = list(db.backups.find().sort('uploaded_at', -1))
        
        # Convertir ObjectId a string para JSON
        for backup in backups:
            backup['_id'] = str(backup['_id'])
            if 'uploaded_by' in backup and backup['uploaded_by']:
                # Obtener información del usuario que subió el respaldo
                user = db.users.find_one({'_id': ObjectId(backup['uploaded_by'])})
                if user:
                    backup['uploaded_by_name'] = user.get('username', 'Desconocido')
            
        return render_template(
            'admin/drive_backups.html',
            backups=backups,
            title='Respaldo en Google Drive',
            active_page='drive_backups'
        )
    except Exception as e:
        current_app.logger.error(f"Error al listar respaldos de Google Drive: {str(e)}", exc_info=True)
        flash('Error al cargar la lista de respaldos de Google Drive', 'error')
        return redirect(url_for('main.dashboard'))

@admin_bp.route("/truncate_log", methods=["POST"])
@admin_required
def truncate_log_route():
    import subprocess
    import sys
    log_file = request.form.get('log_file')
    lines = request.form.get('lines')
    date = request.form.get('date')
    script_path = os.path.join(os.path.dirname(__file__), '../../tools/log_utils.py')
    cmd = [sys.executable, script_path, '--file', log_file]
    if lines:
        cmd += ['--lines', lines]
    elif date:
        cmd += ['--date', date]
    else:
        # Si la petición es AJAX o JSON, responde con JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "error", "message": "Debes indicar número de líneas o fecha."}), 400
        flash('Debes indicar número de líneas o fecha.', 'warning')
        return redirect(url_for('maintenance.maintenance_dashboard'))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            flash(result.stdout, 'success')
        else:
            flash(result.stderr, 'danger')
    except Exception as e:
        flash(f'Error al truncar el log: {str(e)}', 'danger')
    return redirect(url_for('maintenance.maintenance_dashboard'))

# Función para registrar los blueprints
def register_admin_blueprints(app):
    """
    Función para registrar blueprints adicionales de administración.
    Nota: admin_logs_bp ya está registrado en __init__.py
    """
    try:
        # No es necesario registrar admin_logs_bp aquí ya que ya está registrado en __init__.py
        # con el prefijo correcto
        return True
    except Exception as e:
        app.logger.error(f"Error en register_admin_blueprints: {str(e)}")
        return False

app = None
try:
    from flask import current_app
    app = current_app._get_current_object()
except Exception:
    import __main__
    app = getattr(__main__, 'app', None)
if app is not None:
    register_admin_blueprints(app)
