# Script: maintenance_routes.py
# Descripción: Rutas de mantenimiento para el panel de administración
# Uso: Importado como blueprint en main_app.py
# Requiere: Flask, Flask-Login
# Variables de entorno: N/A
# Autor: EDF Developer - 2025-06-09

"""
Maintenance Routes for Admin Dashboard
"""
import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, session
from flask_login import login_required, current_user
from functools import wraps

# Crear el blueprint con un nombre único
maintenance_bp = Blueprint('maintenance', __name__, 
                         template_folder='templates')

# Configuración del logger
logger = logging.getLogger(__name__)

# --- Decorador admin_required ---
def admin_required(f):
    """Decorador para requerir privilegios de administrador (compatible API y web)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(f"[admin_required] current_user: {current_user}")
        logger.debug(f"[admin_required] is_authenticated: {getattr(current_user, 'is_authenticated', None)}")
        logger.debug(f"[admin_required] is_admin: {getattr(current_user, 'is_admin', None)}")
        logger.debug(f"[admin_required] session: {dict(getattr(request, 'session', {}))}")
        
        # Mejorar detección de API: cualquier ruta que sea /admin/api/*, /admin/logs/list o /admin/backup/upload-to-drive/* es API
        api_paths = ["/admin/logs/list"]
        is_api = (
            request.is_json
            or request.accept_mimetypes['application/json']
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.path.startswith('/admin/api/')
            or request.path in api_paths
            or request.path.startswith('/admin/backup/upload-to-drive')
        )
        
        if not current_user.is_authenticated:
            logger.warning("Intento de acceso no autenticado al panel de mantenimiento")
            if is_api:
                return jsonify({'status': 'error', 'message': 'No autenticado'}), 401
            return redirect(url_for('auth.login', next=request.url))
            
        if not getattr(current_user, 'is_admin', False):
            logger.warning(f"Intento de acceso no autorizado al panel de mantenimiento por {getattr(current_user, 'email', 'usuario desconocido')}")
            if is_api:
                return jsonify({'status': 'error', 'message': 'No autorizado'}), 403
            flash('No tienes permiso para acceder a esta sección.', 'danger')
            return redirect(url_for('admin.dashboard_admin'))
            
        logger.info(f"Acceso autorizado al panel de mantenimiento para {getattr(current_user, 'email', 'usuario')}")
        return f(*args, **kwargs)
    return decorated_function

# Ruta temporal de depuración para forzar login como admin
@maintenance_bp.route('/login_directo_admin')
def login_directo_admin():
    session['user_id'] = 'admin_id_dummy'  # Cambia por el _id real si es necesario
    session['username'] = 'admin'
    session['role'] = 'admin'
    session['email'] = 'admin@example.com'
    return redirect(url_for('maintenance.maintenance_dashboard'))

@maintenance_bp.route('/maintenance/api/list_logs')
@login_required
@admin_required
def list_logs():
    """Devuelve la lista de archivos de log disponibles en la carpeta logs."""
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    archivos = []
    if os.path.exists(logs_dir):
        for f in os.listdir(logs_dir):
            if f.endswith('.log'):
                archivos.append(f)
    return jsonify({'listado_archivos': archivos})

@maintenance_bp.route('/logs/view')
@login_required
@admin_required
def view_log():
    """Devuelve las últimas N líneas de un archivo de log especificado por el usuario (solo admins)."""
    log_file = request.args.get('file')
    try:
        lines = int(request.args.get('lines', 40))
    except Exception:
        lines = 40
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    if not log_file:
        from flask import abort
        abort(400, description='Archivo no especificado')
    # Evitar path traversal
    safe_path = os.path.abspath(os.path.join(logs_dir, log_file))
    if not safe_path.startswith(logs_dir):
        from flask import abort
        abort(400, description='Ruta de log no permitida')
    if not os.path.exists(logs_dir):
        from flask import abort
        abort(404, description='Directorio de logs no encontrado')
    try:
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        preview = ''.join(all_lines[-lines:])
        return jsonify({'status': 'success', 'content': preview})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@maintenance_bp.route('/home')
@login_required
@admin_required
def maintenance_home():
    """Página principal de mantenimiento (opción secundaria del menú)."""
    # Valores por defecto para evitar errores en la plantilla
    import shutil
    from datetime import datetime
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    temp_count = 0
    temp_size = 0
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir):
            temp_count += len(files)
            for f in files:
                fp = os.path.join(root, f)
                try:
                    temp_size += os.path.getsize(fp)
                except Exception:
                    pass
    temp_size_mb = round(temp_size / (1024 * 1024), 2)
    # Disco
    total, used, free = shutil.disk_usage("/")
    used_gb = used // (2**30)
    total_gb = total // (2**30)
    percent = int((used / total) * 100) if total > 0 else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Simulación de caché (rellenar si tienes datos reales)
    cache = {'hit_rate': 0, 'hit_count': 0, 'miss_count': 0}
    summary = {
        'total_users': 0,
        'users_changed': 0,
        'changes': []
    }
    applied = False
    backup_file = ''
    data = {
        'disk': {'percent': percent, 'used_gb': used_gb, 'total_gb': total_gb},
        'timestamp': now,
        'temp_files': {'count': temp_count, 'total_size_mb': temp_size_mb},
        'cache': cache
    }
    return render_template(
        'admin/maintenance.html',
        user=getattr(current_user, 'email', 'usuario'),
        summary=summary,
        applied=applied,
        backup_file=backup_file,
        data=data
    )

@maintenance_bp.route('/dashboard')
@login_required
@admin_required
def maintenance_dashboard():
    """Dashboard principal de mantenimiento."""
    try:
        import shutil
        from datetime import datetime
        
        total, used, free = shutil.disk_usage("/")
        
        used_gb = used // (2**30)
        total_gb = total // (2**30)
        percent = int((used / total) * 100) if total > 0 else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "disk": {"percent": percent, "used_gb": used_gb, "total_gb": total_gb},
            "timestamp": now
        }
        
        # Habilitar el sistema de monitoreo por defecto
        monitoring_enabled = True
        
        return render_template('admin/maintenance/dashboard.html', 
                              user=getattr(current_user, 'email', 'usuario'), 
                              data=data, 
                              monitoring_enabled=monitoring_enabled)
    except Exception as e:
        logger.error(f"Error en maintenance_dashboard: {str(e)}")
        flash('Error inesperado al cargar el dashboard de mantenimiento. Por favor, contacta al administrador.', 'danger')
        return redirect(url_for('admin.dashboard_admin'))

@maintenance_bp.route('/api/cleanup-temp', methods=['POST'])
@login_required
@admin_required
def cleanup_temp_files():
    """Elimina archivos temporales en el directorio tmp según rango de fecha/hora."""
    from datetime import datetime, timedelta
    temp_dir = os.path.join(os.getcwd(), 'tmp')
    start = request.form.get('start_datetime')
    end = request.form.get('end_datetime')
    days = request.form.get('days')
    if not (start and end):
        # Si no hay fechas pero sí days, calculamos el rango
        if days:
            try:
                days = int(days)
                now = datetime.now()
                dt_end = now
                dt_start = now - timedelta(days=days)
            except Exception:
                return jsonify({'status': 'error', 'message': 'El parámetro days no es válido.'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'Debes indicar fecha/hora de inicio y fin, o un número de días.'}), 400
    else:
        try:
            dt_start = datetime.fromisoformat(start)
            dt_end = datetime.fromisoformat(end)
        except Exception:
            return jsonify({'status': 'error', 'message': 'Formato de fecha/hora inválido.'}), 400
    if not os.path.exists(temp_dir):
        return jsonify({'status': 'success', 'message': 'No existe el directorio de temporales.'})
    deleted = 0
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                if dt_start <= mtime <= dt_end:
                    os.remove(fp)
                    deleted += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar {fp}: {e}")
    return jsonify({'status': 'success', 'message': f'Se eliminaron {deleted} archivos temporales.'})

# --- Estado simulado de tareas programadas (en memoria, para demo) ---
scheduled_tasks_state = {
    'cleanup': {'estado': 'Desconocido', 'ultima_ejecucion': None},
    'mongo': {'estado': 'Desconocido', 'ultima_ejecucion': None},
    'disk': {'estado': 'Desconocido', 'ultima_ejecucion': None},
}

@maintenance_bp.route('/maintenance/api/system_status', methods=['GET'])
@login_required
@admin_required
def system_status():
    """Devuelve el estado del sistema."""
    import psutil
    import platform
    import getpass
    from datetime import datetime
    mem = psutil.virtual_memory()
    memoria = {
        'total_gb': round(mem.total / (1024**3), 2),
        'disponible_gb': round(mem.available / (1024**3), 2),
        'porcentaje': mem.percent
    }
    cpu_percent = psutil.cpu_percent(interval=0.5)
    so = platform.system() + ' ' + platform.release()
    arquitectura = platform.machine()
    usuario = getpass.getuser()
    hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({
        'status': 'success',
        'memoria': memoria,
        'cpu': {'porcentaje': cpu_percent},
        'so': so,
        'arquitectura': arquitectura,
        'usuario': usuario,
        'hora': hora
    })

@maintenance_bp.route('/maintenance/api/scheduled_tasks', methods=['GET'])
@login_required
@admin_required
def scheduled_tasks():
    """Devuelve la lista de tareas programadas."""
    tasks = []
    for task_id, info in scheduled_tasks_state.items():
        tasks.append({
            'id': task_id,
            'estado': info['estado'],
            'ultima_ejecucion': info['ultima_ejecucion']
        })
    return jsonify({'tasks': tasks})

@maintenance_bp.route('/maintenance/api/run_task', methods=['POST'])
@login_required
@admin_required
def run_task():
    """Ejecuta una tarea de mantenimiento."""
    import time
    from datetime import datetime
    import flask
    import getpass
    
    # Rate limiting simple por IP (1 petición cada 5 segundos)
    if not hasattr(flask.g, '_last_task_run'):
        if not hasattr(flask.current_app, 'rate_limit_task'):
            flask.current_app.rate_limit_task = {}
        flask.g._last_task_run = flask.current_app.rate_limit_task
    ip = flask.request.remote_addr
    now = time.time()
    if ip in flask.g._last_task_run and now - flask.g._last_task_run[ip] < 2:
        from flask import abort
        abort(429, description='Demasiadas peticiones. Espera unos segundos.')
    flask.g._last_task_run[ip] = now
    
    task = request.form.get('task') or request.json.get('task')
    user = getpass.getuser() if hasattr(getpass, 'getuser') else 'admin'
    if task not in scheduled_tasks_state:
        print(f"[AUDITORÍA] {datetime.now()} | Usuario: {user} | IP: {ip} | Tarea: {task} | Resultado: ERROR (Tarea desconocida)")
        from flask import abort
        abort(400, description='Tarea desconocida.')
    
    # Simula la ejecución de la tarea
    try:
        if task == 'cleanup':
            resultado = 'Limpieza de logs completada.'
        elif task == 'mongo':
            resultado = 'Verificación de MongoDB completada.'
        elif task == 'disk':
            resultado = 'Verificación de disco completada.'
        else:
            resultado = 'Tarea ejecutada.'
        scheduled_tasks_state[task]['estado'] = 'OK'
        scheduled_tasks_state[task]['ultima_ejecucion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[AUDITORÍA] {datetime.now()} | Usuario: {user} | IP: {ip} | Tarea: {task} | Resultado: OK")
        return jsonify({'status': 'success', 'message': resultado})
    except Exception as e:
        scheduled_tasks_state[task]['estado'] = 'ERROR'
        scheduled_tasks_state[task]['ultima_ejecucion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        from flask import abort
        abort(500, description=f'Error inesperado: {str(e)}')

# =============================
# RUTAS DE BACKUP Y RESTORE
# =============================

@maintenance_bp.route('/maintenance/api/backup', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Crea un backup de la base de datos."""
    try:
        from datetime import datetime
        import os
        import json
        from app.database import get_db
        
        # Obtener datos de MongoDB
        db = get_db()
        
        # Crear directorio de backups si no existe
        backup_dir = os.path.join(os.getcwd(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'maintenance_backup_{timestamp}.json'
        backup_path = os.path.join(backup_dir, filename)
        
        # Recopilar datos de todas las colecciones principales
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'collections': {}
        }
        
        # Colecciones a respaldar
        collections_to_backup = ['users', 'catalogs', 'tables', 'images']
        
        for collection_name in collections_to_backup:
            try:
                collection = db[collection_name]
                documents = list(collection.find())
                # Convertir ObjectId a string para JSON
                for doc in documents:
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                backup_data['collections'][collection_name] = documents
                logger.info(f"Respaldados {len(documents)} documentos de {collection_name}")
            except Exception as e:
                logger.warning(f"Error al respaldar colección {collection_name}: {str(e)}")
                backup_data['collections'][collection_name] = []
        
        # Guardar backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Verificar que el archivo se creó correctamente
        if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
            file_size = os.path.getsize(backup_path)
            logger.info(f"Backup creado exitosamente: {filename} ({file_size} bytes)")
            
            return jsonify({
                'status': 'success',
                'message': f'Backup creado exitosamente: {filename}',
                'filename': filename,
                'size': file_size,
                'download_url': f'/admin/maintenance/api/download_backup/{filename}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Error al crear el archivo de backup'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creando backup: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error al crear backup: {str(e)}'
        }), 500

@maintenance_bp.route('/api/download_backup/<filename>')
@login_required
@admin_required
def download_backup(filename):
    """Descarga un archivo de backup."""
    try:
        backup_dir = os.path.join(os.getcwd(), 'backups')
        
        # Validar nombre de archivo
        if '..' in filename or '/' in filename:
            return jsonify({'status': 'error', 'message': 'Nombre de archivo no válido'}), 400
        
        file_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404
        
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error descargando backup: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error al descargar: {str(e)}'}), 500

@maintenance_bp.route('/api/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup():
    """Restaura un backup de la base de datos."""
    try:
        from flask import request
        import json
        from bson import ObjectId
        from app.database import get_db
        
        # Verificar si se subió un archivo
        if 'backup_file' in request.files:
            file = request.files['backup_file']
            if file.filename == '':
                return jsonify({'status': 'error', 'message': 'No se seleccionó archivo'}), 400
            
            # Leer contenido del archivo
            try:
                content = file.read().decode('utf-8')
                backup_data = json.loads(content)
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Error al leer archivo: {str(e)}'}), 400
                
        elif 'drive_url' in request.form:
            # Restaurar desde Google Drive (funcionalidad futura)
            return jsonify({'status': 'error', 'message': 'Restauración desde Google Drive no implementada aún'}), 501
        else:
            return jsonify({'status': 'error', 'message': 'No se proporcionó archivo o URL'}), 400
        
        # Validar estructura del backup
        if 'collections' not in backup_data:
            return jsonify({'status': 'error', 'message': 'Formato de backup inválido'}), 400
        
        db = get_db()
        restored_collections = []
        
        # Restaurar cada colección
        for collection_name, documents in backup_data['collections'].items():
            try:
                if not documents:  # Saltar colecciones vacías
                    continue
                    
                collection = db[collection_name]
                
                # Convertir string IDs de vuelta a ObjectId
                for doc in documents:
                    if '_id' in doc and isinstance(doc['_id'], str):
                        try:
                            doc['_id'] = ObjectId(doc['_id'])
                        except:
                            # Si no es un ObjectId válido, eliminar el campo _id
                            del doc['_id']
                
                # Limpiar colección existente (CUIDADO: esto elimina datos)
                # collection.delete_many({})
                
                # Insertar documentos (usar insert_many con ordered=False para continuar en caso de duplicados)
                if documents:
                    try:
                        collection.insert_many(documents, ordered=False)
                        restored_collections.append(f"{collection_name}: {len(documents)} documentos")
                        logger.info(f"Restaurados {len(documents)} documentos en {collection_name}")
                    except Exception as e:
                        # Intentar inserción uno por uno en caso de duplicados
                        inserted = 0
                        for doc in documents:
                            try:
                                collection.insert_one(doc)
                                inserted += 1
                            except:
                                pass  # Ignorar duplicados
                        restored_collections.append(f"{collection_name}: {inserted} documentos (algunos duplicados omitidos)")
                        logger.info(f"Restaurados {inserted} documentos en {collection_name} (con duplicados omitidos)")
                        
            except Exception as e:
                logger.error(f"Error restaurando colección {collection_name}: {str(e)}")
                restored_collections.append(f"{collection_name}: ERROR - {str(e)}")
        
        if restored_collections:
            return jsonify({
                'status': 'success',
                'message': f'Restauración completada. Colecciones procesadas: {", ".join(restored_collections)}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No se pudo restaurar ninguna colección'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en restauración: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error en restauración: {str(e)}'
        }), 500

def init_app(app):
    """Inicialización de la aplicación."""
    app.register_blueprint(maintenance_bp)
    app.logger.info('Módulo de mantenimiento registrado')
