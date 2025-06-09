"""
Maintenance Routes for Admin Dashboard
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps

# Configuración del logger
logger = logging.getLogger(__name__)

# Crear el blueprint con un nombre único
maintenance_bp = Blueprint('maintenance', __name__, 
                         template_folder='templates')

def admin_required(f):
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
    """Panel de dashboard de mantenimiento."""
    try:
        logger.info("Accediendo al dashboard de mantenimiento")
        import shutil
        from datetime import datetime
        # Solo mostrar información de disco y timestamp
        total, used, free = shutil.disk_usage("/")
        used_gb = used // (2**30)
        total_gb = total // (2**30)
        percent = int((used / total) * 100) if total > 0 else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "disk": {"percent": percent, "used_gb": used_gb, "total_gb": total_gb},
            "timestamp": now
        }
        return render_template('admin/maintenance/dashboard.html', user=getattr(current_user, 'email', 'usuario'), data=data)
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
    if not (start and end):
        return jsonify({'status': 'error', 'message': 'Debes indicar fecha/hora de inicio y fin.'}), 400
    try:
        dt_start = datetime.fromisoformat(start)
        dt_end = datetime.fromisoformat(end)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Formato de fecha/hora inválido'}), 400
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


@maintenance_bp.route('/system_status')
@login_required
@admin_required
def system_status():
    """Obtiene el estado del sistema."""
    try:
        cmd = [
            os.path.join(os.getcwd(), '.venv310', 'bin', 'python3'),
            os.path.join(os.getcwd(), 'scripts', 'maintenance', 'run_maintenance.py'),
            '--task', 'disk'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            try:
                # Intentar parsear la salida como JSON
                status_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver la salida como texto
                status_data = {'output': result.stdout}
                
            return jsonify({
                'status': 'success',
                'data': status_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.stderr or 'Error al obtener el estado del sistema'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }), 500

def init_app(app):
    """Inicialización de la aplicación."""
    app.register_blueprint(maintenance_bp)
    app.logger.info('Módulo de mantenimiento registrado')
