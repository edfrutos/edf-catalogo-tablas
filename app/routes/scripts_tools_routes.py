# Script: scripts_tools_routes.py
# Descripción: Rutas para la gestión de scripts y herramientas
# Autor: Equipo de Desarrollo - 2025-06-17

import os
import logging
import subprocess
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
    {'name': 'tools', 'path': os.path.join(BASE_PATH, 'tools')}
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
    if 'user_id' not in session or not session.get('logged_in', False):
        return False
    # Verificar si el usuario tiene rol de admin
    if session.get('role') != 'admin':
        return False
    return True

@scripts_tools_bp.route('/list')
def list_files():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'No tienes permisos para acceder a esta función'}), 403
    """
    Endpoint para listar archivos de scripts, tests y tools.
    
    Query params:
        page (int): Número de página (default: 1)
        per_page (int): Elementos por página (default: 20)
        filetype (str): Filtro por tipo de archivo (opcional)
        
    Returns:
        JSON: Listado de archivos por directorio
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        filetype = request.args.get('filetype')
        
        result = {}
        for info in DIRECTORY_INFOS:
            result[info['name']] = list_files_with_info(info['path'], page=page, per_page=per_page, filetype=filetype)
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en list_files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@scripts_tools_bp.route('/run', methods=['POST'])
def run_script():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'No tienes permisos para acceder a esta función'}), 403
    data = request.get_json()
    rel_path = data.get('rel_path')
    args = data.get('args', [])
    shell = bool(data.get('shell', False))
    if not rel_path or '..' in rel_path or rel_path.startswith('/'):
        return jsonify({'success': False, 'error': 'Ruta no permitida'}), 400
    abs_path = os.path.join(BASE_PATH, rel_path)
    if not os.path.isfile(abs_path):
        return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
    # Solo permitir .py y .sh, advertir si es .sh
    if abs_path.endswith('.py'):
        cmd = ['python3', abs_path] + args
    elif abs_path.endswith('.sh'):
        cmd = ['bash', abs_path] + args
        shell = True
    else:
        return jsonify({'success': False, 'error': 'Solo se pueden ejecutar scripts Python o Shell'}), 400
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=False)
        warning = ''
        if abs_path.endswith('.sh'):
            warning = '¡Precaución! Estás ejecutando un script de shell. Asegúrate de confiar en el contenido.'
        return jsonify({
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode,
            'warning': warning
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@scripts_tools_bp.route('/download', methods=['GET'])
def download_file():
    # Verificar si el usuario es admin
    if not check_admin():
        return jsonify({'error': 'No tienes permisos para acceder a esta función'}), 403
    rel_path = request.args.get('rel_path')
    if not rel_path or '..' in rel_path or rel_path.startswith('/'):
        return 'Ruta no permitida', 400
    abs_path = os.path.join(BASE_PATH, rel_path)
    if not os.path.isfile(abs_path):
        return 'Archivo no encontrado', 404
    from flask import send_file
    return send_file(abs_path, as_attachment=True)
