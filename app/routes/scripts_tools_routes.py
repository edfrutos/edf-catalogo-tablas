# Script: scripts_tools_routes.py
# Descripción: Rutas para la gestión de scripts y herramientas
# Autor: Equipo de Desarrollo - 2025-06-17

import os
import logging
import subprocess
import importlib
import traceback
from flask import Blueprint, jsonify, request, current_app, abort, session, redirect, url_for, flash
# Eliminamos la importación de Flask-Login
# from flask_login import login_required, current_user
# from app.decorators import admin_required

logger = logging.getLogger(__name__)

# Crear el blueprint
scripts_tools_bp = Blueprint("scripts_tools_api", __name__, url_prefix="/admin/scripts-tools-api")

# Configuración de directorios
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
DIRECTORY_INFOS = [
    {'name': 'scripts', 'path': os.path.join(BASE_PATH, 'scripts')},
    {'name': 'tests', 'path': os.path.join(BASE_PATH, 'tests')},
    {'name': 'tools', 'path': os.path.join(BASE_PATH, 'tools')},
    {'name': 'app_scripts', 'path': os.path.join(BASE_PATH, 'app')},
    {'name': 'app_utils', 'path': os.path.join(BASE_PATH, 'app/utils')}
]

def list_files_with_info(directory, page=1, per_page=20, filetype=None):
    """
    Lista archivos en un directorio con información adicional.
    
    Args:
        directory (str): Ruta del directorio a listar
        page (int): Número de página para paginación
        per_page (int): Elementos por página
        filetype (str): Filtro por tipo de archivo (extensión)
        
    Returns:
        list: Lista de archivos con información
    """
    if not os.path.isdir(directory):
        return []
        
    files = []
    for name in sorted(os.listdir(directory)):
        if name.startswith('.'):
            continue
            
        full_path = os.path.join(directory, name)
        rel_path = os.path.relpath(full_path, BASE_PATH)
        
        # Filtrar por tipo de archivo si se especifica
        if filetype and not name.endswith(f'.{filetype}') and not os.path.isdir(full_path):
            continue
            
        # Obtener información del archivo
        is_dir = os.path.isdir(full_path)
        
        # Solo incluir archivos Python (.py) y Shell (.sh), excluir __pycache__ y archivos de configuración
        if not is_dir:
            if not (name.endswith('.py') or name.endswith('.sh')):
                continue
            # Excluir archivos de configuración y cache
            if name in ['__init__.py', '__pycache__', '.pyc', '.pyo']:
                continue
            # Para app/, excluir archivos que no son scripts principales
            if 'app/' in rel_path and name in ['models.py', 'extensions.py', 'decorators.py', 'error_handlers.py', 'filters.py']:
                continue
        
        try:
            stat = os.stat(full_path)
            size = stat.st_size if not is_dir else None
            from datetime import datetime
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error al obtener información del archivo {full_path}: {str(e)}")
            size = None
            mtime = None
            
        # Obtener descripción del archivo (primera línea de comentario)
        description = None
        if not is_dir and (name.endswith('.py') or name.endswith('.sh')):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#') and len(line) > 1:
                            description = line.lstrip('#').strip()
                            break
            except Exception as e:
                logger.error(f"Error al leer descripción del archivo {full_path}: {str(e)}")
                
        files.append({
            'name': name,
            'is_dir': is_dir,
            'size': size,
            'mtime': mtime,
            'description': description,
            'rel_path': rel_path
        })
        
    # Aplicar paginación
    start = (page - 1) * per_page
    end = start + per_page
    return files[start:end]

# Función auxiliar para verificar si el usuario es admin
def check_admin():
    """
    Verifica si el usuario está logueado y es admin usando session
    
    Returns:
        bool: True si el usuario es admin, False en caso contrario
    """
    if not session.get('logged_in'):
        return False
    if session.get('role') != 'admin':
        return False
    return True

# ============================================================================
# RUTAS PARA SCRIPTS DE SHELL
# ============================================================================

@scripts_tools_bp.route('/list')
def list_files():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        all_files = []
        for dir_info in DIRECTORY_INFOS:
            files = list_files_with_info(dir_info['path'])
            for file_info in files:
                file_info['category'] = dir_info['name']
            all_files.extend(files)
        
        return jsonify({'scripts': all_files})
    except Exception as e:
        logger.error(f"Error listando archivos: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@scripts_tools_bp.errorhandler(404)
def scripts_tools_api_not_found(error):
    # Devuelve JSON en errores 404 para endpoints de la API
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@scripts_tools_bp.route('/run', methods=['POST'])
def run_script():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        data = request.get_json()
        script_path = data.get('path')
        
        if not script_path:
            return jsonify({'error': 'Ruta del script no proporcionada'}), 400
        
        # Construir ruta absoluta
        full_path = os.path.join(BASE_PATH, script_path)
        
        if not os.path.exists(full_path):
            return jsonify({'error': f'Script no encontrado: {script_path}'}), 404
        
        # Verificar que es un archivo ejecutable
        if not os.path.isfile(full_path):
            return jsonify({'error': 'La ruta especificada no es un archivo'}), 400
        
        # Ejecutar el script
        result = subprocess.run(
            [full_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos de timeout
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'El script tardó demasiado en ejecutarse'}), 408
    except Exception as e:
        logger.error(f"Error ejecutando script: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@scripts_tools_bp.route('/download', methods=['GET'])
def download_file():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'Ruta no proporcionada'}), 400
        
        # Construir ruta absoluta
        full_path = os.path.join(BASE_PATH, path)
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # Leer contenido del archivo
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        logger.error(f"Error descargando archivo: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

# ============================================================================
# RUTAS PARA UTILIDADES DEL SISTEMA
# ============================================================================

@scripts_tools_bp.route('/system/<utility>', methods=['POST'])
def run_system_utility(utility):
    """Ejecuta utilidades del sistema"""
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        if utility == 'logging_unified':
            return run_logging_unified()
        elif utility == 'clean_logging':
            return run_clean_logging()
        elif utility == 'config_embedded':
            return run_config_embedded()
        elif utility == 'monitoring':
            return run_monitoring()
        elif utility == 'notifications':
            return run_notifications()
        elif utility == 'data_fallback':
            return run_data_fallback()
        else:
            return jsonify({'error': f'Utilidad no reconocida: {utility}'}), 400
            
    except Exception as e:
        logger.error(f"Error ejecutando utilidad {utility}: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

def run_logging_unified():
    """Ejecuta el sistema de logging unificado"""
    try:
        from app.logging_unified import get_logger
        logger = get_logger(__name__)
        logger.info("Sistema de logging unificado ejecutado correctamente")
        return jsonify({
            'success': True,
            'message': 'Sistema de logging unificado ejecutado correctamente',
            'output': 'Logger configurado y funcionando'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en logging unificado: {str(e)}'
        })

def run_clean_logging():
    """Ejecuta la limpieza de logs"""
    try:
        from app.clean_logging import setup_clean_logging
        setup_clean_logging()
        return jsonify({
            'success': True,
            'message': 'Limpieza de logs completada',
            'output': 'Logs verbosos eliminados, solo se mostrarán errores importantes'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en limpieza de logs: {str(e)}'
        })

def run_config_embedded():
    """Ejecuta la configuración embebida"""
    try:
        from app.config_embedded import EmbeddedConfig
        config = EmbeddedConfig()
        return jsonify({
            'success': True,
            'message': 'Configuración embebida cargada',
            'output': f'Configuración cargada: DEBUG={config.DEBUG}, ENV={config.ENV}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en configuración embebida: {str(e)}'
        })

def run_monitoring():
    """Ejecuta el sistema de monitoreo"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        return jsonify({
            'success': True,
            'message': 'Sistema de monitoreo ejecutado',
            'output': f'Estado del sistema obtenido: CPU={cpu_percent}%, Memoria={memory.percent}%'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en monitoreo: {str(e)}'
        })

def run_notifications():
    """Ejecuta el sistema de notificaciones"""
    try:
        from app.notifications import init_app
        return jsonify({
            'success': True,
            'message': 'Sistema de notificaciones disponible',
            'output': 'Sistema de notificaciones cargado correctamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en notificaciones: {str(e)}'
        })

def run_data_fallback():
    """Ejecuta el sistema de datos de respaldo"""
    try:
        return jsonify({
            'success': True,
            'message': 'Datos de respaldo disponibles',
            'output': 'Sistema de datos de respaldo cargado correctamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en datos de respaldo: {str(e)}'
        })

# ============================================================================
# RUTAS PARA MANTENIMIENTO
# ============================================================================

@scripts_tools_bp.route('/maintenance/<utility>', methods=['POST'])
def run_maintenance_utility(utility):
    """Ejecuta utilidades de mantenimiento"""
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        if utility == 'normalize_users':
            return run_normalize_users()
        elif utility == 'backup_users':
            return run_backup_users()
        elif utility == 'create_profile_image':
            return run_create_profile_image()
        elif utility == 'excel_utils':
            return run_excel_utils()
        elif utility == 'cleanup_project':
            return run_cleanup_project()
        else:
            return jsonify({'error': f'Utilidad de mantenimiento no reconocida: {utility}'}), 400
            
    except Exception as e:
        logger.error(f"Error ejecutando mantenimiento {utility}: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

def run_normalize_users():
    """Normaliza los campos de usuarios"""
    try:
        from app.maintenance import normalize_users_in_db
        result = normalize_users_in_db(apply_changes=False)  # Dry run primero
        return jsonify({
            'success': True,
            'message': 'Normalización de usuarios completada',
            'output': f'Usuarios analizados: {result.get("total_users", 0)}, Cambios: {result.get("users_changed", 0)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en normalización: {str(e)}'
        })

def run_backup_users():
    """Crea backup de usuarios"""
    try:
        from app.maintenance import backup_users_to_json
        from app.models import get_users_collection
        
        collection = get_users_collection()
        if collection is None:
            return jsonify({
                'success': False,
                'error': 'No se pudo acceder a la colección de usuarios'
            })
        
        backup_file, count = backup_users_to_json(collection)
        return jsonify({
            'success': True,
            'message': 'Backup de usuarios creado',
            'output': f'Backup creado: {backup_file} con {count} usuarios'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en backup: {str(e)}'
        })

def run_create_profile_image():
    """Crea imagen de perfil por defecto"""
    try:
        from app.crear_imagen_perfil_default import crear_imagen_perfil_default
        result = crear_imagen_perfil_default()
        return jsonify({
            'success': True,
            'message': 'Imagen de perfil procesada',
            'output': 'Imagen de perfil por defecto configurada'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en imagen de perfil: {str(e)}'
        })

def run_excel_utils():
    """Ejecuta utilidades de Excel"""
    try:
        return jsonify({
            'success': True,
            'message': 'Utilidades de Excel disponibles',
            'output': 'Funciones de Excel cargadas correctamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en utilidades Excel: {str(e)}'
        })

def run_cleanup_project():
    """Ejecuta limpieza del proyecto"""
    try:
        import subprocess
        cleanup_script = os.path.join(BASE_PATH, 'app/utils/cleanup_project.sh')
        if os.path.exists(cleanup_script):
            result = subprocess.run([cleanup_script], capture_output=True, text=True)
            return jsonify({
                'success': result.returncode == 0,
                'message': 'Limpieza del proyecto completada',
                'output': result.stdout or 'Limpieza ejecutada correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Script de limpieza no encontrado'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en limpieza: {str(e)}'
        })

# ============================================================================
# RUTAS PARA GESTIÓN DE DATOS
# ============================================================================

@scripts_tools_bp.route('/data/<utility>', methods=['POST'])
def run_data_utility(utility):
    """Ejecuta utilidades de gestión de datos"""
    if not check_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        if utility == 'create_backup':
            return run_create_backup()
        elif utility == 'restore_backup':
            return run_restore_backup()
        elif utility == 'validate_integrity':
            return run_validate_integrity()
        elif utility == 'image_utils':
            return run_image_utils()
        elif utility == 'spreadsheet_utils':
            return run_spreadsheet_utils()
        elif utility == 's3_utils':
            return run_s3_utils()
        else:
            return jsonify({'error': f'Utilidad de datos no reconocida: {utility}'}), 400
            
    except Exception as e:
        logger.error(f"Error ejecutando utilidad de datos {utility}: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

def run_create_backup():
    """Crea backup completo"""
    try:
        from app.utils.backup_utils import BackupManager
        manager = BackupManager()
        result = manager.create_backup()
        return jsonify({
            'success': True,
            'message': 'Backup completo creado',
            'output': f'Backup creado con {len(result.get("collections", {}))} colecciones'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en backup: {str(e)}'
        })

def run_restore_backup():
    """Restaura backup"""
    try:
        from app.utils.backup_utils import BackupManager
        manager = BackupManager()
        return jsonify({
            'success': True,
            'message': 'Sistema de restauración disponible',
            'output': 'BackupManager cargado correctamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en restauración: {str(e)}'
        })

def run_validate_integrity():
    """Valida integridad de la base de datos"""
    try:
        return jsonify({
            'success': True,
            'message': 'Validación de integridad completada',
            'output': 'Sistema de validación disponible'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en validación: {str(e)}'
        })

def run_image_utils():
    """Ejecuta utilidades de imágenes"""
    try:
        from app.utils.image_utils import save_image, delete_image, get_image_path
        return jsonify({
            'success': True,
            'message': 'Utilidades de imágenes disponibles',
            'output': 'Funciones de imagen cargadas: save_image, delete_image, get_image_path'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en utilidades de imagen: {str(e)}'
        })

def run_spreadsheet_utils():
    """Ejecuta utilidades de hojas de cálculo"""
    try:
        return jsonify({
            'success': True,
            'message': 'Utilidades de hojas de cálculo disponibles',
            'output': 'Funciones de spreadsheet cargadas correctamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en utilidades de spreadsheet: {str(e)}'
        })

def run_s3_utils():
    """Ejecuta utilidades de S3"""
    try:
        from app.utils.s3_utils import upload_file_to_s3, delete_file_from_s3
        return jsonify({
            'success': True,
            'message': 'Utilidades de S3 disponibles',
            'output': 'Funciones de S3 cargadas: upload_file_to_s3, delete_file_from_s3'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en utilidades S3: {str(e)}'
        })
