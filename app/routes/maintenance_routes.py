# Script: maintenance_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 maintenance_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-09

"""
Maintenance Routes for Admin Dashboard
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, session
from flask_login import login_required, current_user
from functools import wraps

# Crear el blueprint con un nombre único
maintenance_bp = Blueprint('maintenance', __name__, 
                         template_folder='templates')

# Ruta temporal de depuración para forzar login como admin
@maintenance_bp.route('/login_directo_admin')
def login_directo_admin():
    session['user_id'] = 'admin_id_dummy'  # Cambia por el _id real si es necesario
    session['username'] = 'admin'
    session['role'] = 'admin'
    session['email'] = 'admin@example.com'
    return redirect(url_for('maintenance.maintenance_dashboard'))

# Configuración del logger
logger = logging.getLogger(__name__)

# --- Decorador admin_required ---
def admin_required(f):
    """Decorador para requerir privilegios de administrador (compatible API y web)."""
    from functools import wraps
    from flask import request, jsonify, redirect, url_for, flash
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

# --- FIN Decorador admin_required ---

@maintenance_bp.route('/api/list_logs')
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
    from flask import request  # Fix UnboundLocalError
    """Devuelve las últimas N líneas de un archivo de log especificado por el usuario (solo admins)."""
    log_file = request.args.get('file')
    try:
        lines = int(request.args.get('lines', 40))
    except Exception:
        lines = 40
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
    if not log_file:
        return jsonify({'status': 'error', 'message': 'Archivo no especificado'}), 400
    # Evitar path traversal
    safe_path = os.path.abspath(os.path.join(logs_dir, log_file))
    if not safe_path.startswith(logs_dir):
        return jsonify({'status': 'error', 'message': 'Ruta de log no permitida'}), 400
    if not os.path.isfile(safe_path):
        return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404
    try:
        with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        preview = ''.join(all_lines[-lines:])
        return jsonify({'status': 'success', 'content': preview})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



    """
    Ejecuta una tarea de mantenimiento ('cleanup', 'mongo', 'disk') usando el script correspondiente.
    Devuelve el resultado como JSON.
    """
    import subprocess
    from flask import request
    data = request.get_json() if request.is_json else request.form
    task = data.get('task')
    allowed_tasks = {'cleanup', 'mongo', 'disk'}
    if task not in allowed_tasks:
        logger.warning(f"Intento de ejecución de tarea inválida: {task}")
        return jsonify({'status': 'error', 'message': 'Tarea no válida'}), 400
    script_path = os.path.join(os.getcwd(), 'scripts', 'maintenance', 'run_maintenance.py')
    if not os.path.isfile(script_path):
        logger.error(f"Script de mantenimiento no encontrado: {script_path}")
        return jsonify({'status': 'error', 'message': 'Script de mantenimiento no encontrado'}), 500
    cmd = [
        os.path.join(os.getcwd(), '.venv310', 'bin', 'python3'),
        script_path,
        '--task', task
    ]
    try:
        logger.info(f"Ejecutando tarea de mantenimiento: {task} (usuario: {getattr(current_user, 'email', 'desconocido')})")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        logger.info(f"Resultado tarea {task}: returncode={result.returncode}")
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'task': task,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }), (200 if result.returncode == 0 else 500)
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout al ejecutar la tarea {task}")
        return jsonify({'status': 'error', 'message': 'La tarea tardó demasiado en ejecutarse'}), 500
    except Exception as e:
        logger.error(f"Error al ejecutar tarea {task}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

        logger.debug(f"[admin_required] current_user: {current_user}")
        logger.debug(f"[admin_required] is_authenticated: {getattr(current_user, 'is_authenticated', None)}")
        logger.debug(f"[admin_required] is_admin: {getattr(current_user, 'is_admin', None)}")
        from flask import session
        logger.debug(f"[admin_required] session: {dict(session)}")
        if not current_user.is_authenticated:
            logger.warning("Intento de acceso no autenticado al panel de mantenimiento")
            return redirect(url_for('auth.login', next=request.url))
        if not getattr(current_user, 'is_admin', False):
            logger.warning(f"Intento de acceso no autorizado al panel de mantenimiento por {getattr(current_user, 'email', 'usuario desconocido')}")
            flash('No tienes permiso para acceder a esta sección.', 'danger')
            return redirect(url_for('admin.dashboard_admin'))
        logger.info(f"Acceso autorizado al panel de mantenimiento para {getattr(current_user, 'email', 'usuario')}")
        return f(*args, **kwargs)
    return decorated_function

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

    """Decorador para requerir privilegios de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(f"[admin_required] current_user: {current_user}")
        logger.debug(f"[admin_required] is_authenticated: {getattr(current_user, 'is_authenticated', None)}")
        logger.debug(f"[admin_required] is_admin: {getattr(current_user, 'is_admin', None)}")
        from flask import session
        logger.debug(f"[admin_required] session: {dict(session)}")
        if not current_user.is_authenticated:
            logger.warning("Intento de acceso no autenticado al panel de mantenimiento")
            return redirect(url_for('auth.login', next=request.url))
        if not getattr(current_user, 'is_admin', False):
            logger.warning(f"Intento de acceso no autorizado al panel de mantenimiento por {getattr(current_user, 'email', 'usuario desconocido')}")
            flash('No tienes permiso para acceder a esta sección.', 'danger')
            return redirect(url_for('admin.dashboard_admin'))
        logger.info(f"Acceso autorizado al panel de mantenimiento para {getattr(current_user, 'email', 'usuario')}")
        return f(*args, **kwargs)
    return decorated_function

@maintenance_bp.route('/dashboard')
@login_required
@admin_required
def maintenance_dashboard():
    
    
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
        
        
        monitoring_enabled = getattr(current_app, 'monitoring_enabled', False)
        
        
        return render_template('admin/maintenance/dashboard.html', user=getattr(current_user, 'email', 'usuario'), data=data, monitoring_enabled=monitoring_enabled)
    except Exception as e:
        logger.error(f"Error en maintenance_dashboard: {str(e)}")
        
        flash('Error inesperado al cargar el dashboard de mantenimiento. Por favor, contacta al administrador.', 'danger')
        return redirect(url_for('admin.dashboard_admin'))

@maintenance_bp.route('/api/cleanup-temp', methods=['POST'])
@login_required
@admin_required
def cleanup_temp_files():
    """Elimina archivos temporales en el directorio tmp según rango de fecha/hora."""
    from datetime import datetime
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

@maintenance_bp.route('/api/system_status', methods=['GET'])
@login_required
@admin_required
def system_status():
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

@maintenance_bp.route('/api/scheduled_tasks', methods=['GET'])
@login_required
@admin_required
def scheduled_tasks():
    # Devuelve la lista de tareas programadas
    tasks = []
    for task_id, info in scheduled_tasks_state.items():
        tasks.append({
            'id': task_id,
            'estado': info['estado'],
            'ultima_ejecucion': info['ultima_ejecucion']
        })
    return jsonify({'tasks': tasks})

@maintenance_bp.route('/api/run_task', methods=['POST'])
@login_required
@admin_required
def run_task():
    import time
    from datetime import datetime
    import flask
    import getpass
    # Rate limiting simple por IP (1 petición cada 5 segundos)
    if not hasattr(flask.g, '_last_task_run'):
        if not hasattr(flask.current_app, 'rate_limit_task'): flask.current_app.rate_limit_task = {}
        flask.g._last_task_run = flask.current_app.rate_limit_task
    ip = flask.request.remote_addr
    now = time.time()
    if ip in flask.g._last_task_run and now - flask.g._last_task_run[ip] < 2:
        return jsonify({'status': 'error', 'message': 'Demasiadas peticiones. Espera unos segundos.'}), 429
    flask.g._last_task_run[ip] = now
    # ---
    task = request.form.get('task') or request.json.get('task')
    user = getpass.getuser() if hasattr(getpass, 'getuser') else 'admin'
    if task not in scheduled_tasks_state:
        print(f"[AUDITORÍA] {datetime.now()} | Usuario: {user} | IP: {ip} | Tarea: {task} | Resultado: ERROR (Tarea desconocida)")
        return jsonify({'status': 'error', 'message': 'Tarea desconocida.'}), 400
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
        
        return jsonify({'status': 'error', 'message': str(e)})



            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }), 500

def init_app(app):
    """Inicialización de la aplicación."""
    app.register_blueprint(maintenance_bp)
    app.logger.info('Módulo de mantenimiento registrado')
