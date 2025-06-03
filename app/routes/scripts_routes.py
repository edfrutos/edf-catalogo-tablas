#!/usr/bin/env python3
# app/routes/scripts_routes.py

import os
import sys
import glob
import subprocess
import json
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, jsonify, request, abort, session, redirect, url_for, flash, current_app, send_file
from functools import wraps

# Definición local del decorador admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") != "admin":
            flash("No tiene permisos para acceder a esta página", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# Utilizamos la definición local del decorador admin_required

# Definir el directorio raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Definir el directorio de herramientas donde se encuentran las copias de los scripts
TOOLS_DIR = os.path.join(ROOT_DIR, 'tools')

# Crear el blueprint
scripts_bp = Blueprint('scripts', __name__, url_prefix='/admin/tools')

# Ruta alternativa para ejecutar scripts sin path variables
@scripts_bp.route('/execute', methods=['POST'])
@admin_required
def execute_script():
    """Ejecuta un script especificado por parámetro y devuelve su salida"""
    try:
        # Obtener la ruta del script desde los parámetros del formulario o JSON
        if request.is_json:
            data = request.get_json()
            script_path = data.get('script_path', '')
        else:
            script_path = request.form.get('script_path', '')
        
        print(f"\n=== Iniciando ejecución de script (método alternativo) ===")
        print(f"Script solicitado: {script_path}")
        print(f"URL completa: {request.url}")
        print(f"Método: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        
        # Obtener la ruta absoluta del script
        abs_script_path = get_script_path(script_path)
        print(f"Ruta absoluta del script: {abs_script_path}")
        
        if not abs_script_path:
            print(f"\n❌ ERROR: Script no encontrado: {script_path}")
            return jsonify({
                'script': os.path.basename(script_path) if script_path else 'desconocido',
                'error': f'Script no encontrado: {script_path}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 404
        
        # Verificar que el script existe y es ejecutable
        if not os.path.isfile(abs_script_path):
            print(f"\n❌ ERROR: No es un archivo regular: {abs_script_path}")
            return jsonify({
                'script': os.path.basename(abs_script_path),
                'error': f'No es un archivo válido: {abs_script_path}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 400
        
        if not os.access(abs_script_path, os.X_OK):
            print(f"\n❌ ERROR: Script no ejecutable: {abs_script_path}")
            # Intentar corregir los permisos
            try:
                os.chmod(abs_script_path, 0o755)
                print(f"Permisos corregidos para: {abs_script_path}")
            except Exception as e:
                print(f"No se pudieron corregir los permisos: {str(e)}")
                return jsonify({
                    'script': os.path.basename(abs_script_path),
                    'error': f'Script no tiene permisos de ejecución: {abs_script_path}',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 403
        
        # Establecer el tiempo máximo para la ejecución del script
        timeout = 60  # segundos
        
        try:
            print(f"\n✅ Ejecutando script: {abs_script_path}")
            # Ejecutar el script capturando la salida estándar y de error
            process = subprocess.run(
                [abs_script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # No levantar excepción si el comando falla
            )
            
            # Obtener la salida y el código de salida
            output = process.stdout
            error_output = process.stderr
            exit_code = process.returncode
            
            print(f"Código de salida: {exit_code}")
            print(f"Salida:\n{output}")
            
            if error_output:
                print(f"Error:\n{error_output}")
            
            # Devolver la respuesta en formato JSON
            return jsonify({
                'script': os.path.basename(abs_script_path),
                'output': output,
                'error': error_output,
                'exit_code': exit_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except subprocess.TimeoutExpired:
            print(f"\n❌ ERROR: Tiempo de ejecución excedido ({timeout}s): {abs_script_path}")
            return jsonify({
                'script': os.path.basename(abs_script_path),
                'error': f'Tiempo de ejecución excedido ({timeout}s)',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 408
    except Exception as e:
        print(f"\n❌ Excepción al ejecutar el script: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'script': os.path.basename(script_path) if 'script_path' in locals() else 'desconocido',
            'error': f'Error al ejecutar el script: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

def get_script_path(script_path):
    """Obtiene la ruta completa del script evitando duplicaciones de rutas"""
    # Si ya es una ruta absoluta que contiene ROOT_DIR, usarla directamente
    if os.path.isabs(script_path) and ROOT_DIR in script_path:
        return script_path
    
    # Si es una ruta absoluta pero no contiene ROOT_DIR, usarla directamente
    if os.path.isabs(script_path):
        return script_path
    
    # Lista de posibles ubicaciones para buscar el script
    possible_paths = [
        # Ruta directa
        os.path.join(ROOT_DIR, script_path),
        # En directorio tools
        os.path.join(ROOT_DIR, 'tools', script_path),
        # En directorio scripts
        os.path.join(ROOT_DIR, 'scripts', script_path),
    ]
    
    # Buscar en subdirectorios comunes
    for subdir in ['maintenance', 'admin_utils', 'backup', 'monitoring', 'security', 'database']:
        possible_paths.append(os.path.join(ROOT_DIR, 'tools', subdir, script_path))
        possible_paths.append(os.path.join(ROOT_DIR, 'scripts', subdir, script_path))
    
    # Verificar cada ruta posible
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Script encontrado en: {path}")
            return path
    
    # Si no se encuentra, devolver la ruta original
    print(f"Script no encontrado: {script_path}")
    return os.path.join(ROOT_DIR, script_path)

@scripts_bp.route('/view/<path:script_path>')
@admin_required
def view_script_content(script_path):
    """Muestra el contenido de un script"""
    # Utilizar la función get_script_path para normalizar la ruta
    abs_script_path = get_script_path(script_path)
    
    print(f"Intentando acceder al script: {abs_script_path}")
    
    # Verificar que el script existe
    if not os.path.exists(abs_script_path):
        flash('Script no encontrado: ' + abs_script_path, 'error')
        return redirect(url_for('scripts.tools_dashboard'))
    
    # Verificar que el script está dentro del directorio del proyecto
    if not abs_script_path.startswith(ROOT_DIR):
        flash('Script fuera del directorio del proyecto: ' + abs_script_path, 'error')
        return redirect(url_for('scripts.tools_dashboard'))
    
    try:
        # Leer el contenido del script
        with open(abs_script_path, 'r') as f:
            script_content = f.read()
        
        return render_template('script_content.html', 
                              script_name=os.path.basename(abs_script_path),
                              script_path=abs_script_path,
                              script_content=script_content)
    except Exception as e:
        flash(f'Error al leer el contenido del script: {str(e)}', 'error')
        return redirect(url_for('scripts.tools_dashboard'))

@scripts_bp.route('/')
@admin_required
def tools_dashboard():
    """Ruta para acceder al gestor de scripts del sistema"""
    # Definir el directorio de scripts principal (ahora usando el directorio de herramientas)
    tools_dir = TOOLS_DIR
    
    # Definir las categorías de scripts y sus subdirectorios
    script_categories = {
        'maintenance': {
            'name': 'Mantenimiento',
            'description': 'Scripts para iniciar, supervisar y mantener la aplicación',
            'path': os.path.join(tools_dir, 'maintenance'),
            'color': 'primary'
        },
        'admin_utils': {
            'name': 'Utilidades de Admin',
            'description': 'Scripts para administración del sistema',
            'path': os.path.join(tools_dir, 'admin_utils'),
            'color': 'danger'
        },
        'app_runners': {
            'name': 'Ejecutores de App',
            'description': 'Scripts para ejecutar diferentes versiones de la aplicación',
            'path': os.path.join(tools_dir, 'app_runners'),
            'color': 'success'
        },
        'aws_utils': {
            'name': 'Utilidades AWS',
            'description': 'Scripts para interactuar con servicios de AWS',
            'path': os.path.join(tools_dir, 'aws_utils'),
            'color': 'warning'
        },
        'catalog_utils': {
            'name': 'Utilidades de Catálogo',
            'description': 'Scripts para gestionar catálogos',
            'path': os.path.join(tools_dir, 'catalog_utils'),
            'color': 'info'
        },
        'test_scripts': {
            'name': 'Scripts de Prueba',
            'description': 'Scripts simples para probar la funcionalidad',
            'path': os.path.join(tools_dir, 'test_scripts'),
            'color': 'secondary'
        },
        'db_utils': {
            'name': 'Utilidades de BD',
            'description': 'Scripts para gestionar la base de datos',
            'path': os.path.join(tools_dir, 'db_utils'),
            'color': 'secondary'
        },
        'image_utils': {
            'name': 'Utilidades de Imágenes',
            'description': 'Scripts para procesar imágenes',
            'path': os.path.join(tools_dir, 'image_utils'),
            'color': 'dark'
        },
        'monitoring': {
            'name': 'Monitoreo',
            'description': 'Scripts para monitorear el sistema',
            'path': os.path.join(tools_dir, 'monitoring'),
            'color': 'warning'
        },
        'password_utils': {
            'name': 'Utilidades de Contraseñas',
            'description': 'Scripts para gestionar contraseñas',
            'path': os.path.join(tools_dir, 'password_utils'),
            'color': 'danger'
        },
        'session_utils': {
            'name': 'Utilidades de Sesión',
            'description': 'Scripts para gestionar sesiones',
            'path': os.path.join(tools_dir, 'session_utils'),
            'color': 'warning'
        },
        'root': {
            'name': 'Scripts Raíz',
            'description': 'Scripts en el directorio raíz',
            'path': os.path.join(tools_dir, 'root'),
            'color': 'secondary'
        }
    }
    
    # Recopilar todos los scripts
    scripts = []
    
    # Procesar cada categoría
    for category_id, category_info in script_categories.items():
        path = category_info['path']
        print(f"Buscando scripts en: {path}")
        
        if os.path.exists(path):
            # Buscar scripts .sh y .py
            scripts_sh = glob.glob(os.path.join(path, '*.sh'))
            scripts_py = glob.glob(os.path.join(path, '*.py'))
            category_scripts = scripts_sh + scripts_py
            
            # Si es la categoría 'root', excluir scripts que están en subdirectorios
            if category_id == 'root':
                category_scripts = [s for s in category_scripts if os.path.dirname(s) == path]
            
            print(f"Scripts encontrados en {category_id}: {len(category_scripts)}")
            
            for script_path in category_scripts:
                # Verificar que el script existe y es funcional
                if not os.path.isfile(script_path):
                    continue
                script_name = os.path.basename(script_path)
                script_ext = os.path.splitext(script_name)[1]
                # Solo mostrar .sh si es ejecutable, .py si es legible
                if script_ext == '.sh' and not os.access(script_path, os.X_OK):
                    continue
                if script_ext == '.py':
                    try:
                        with open(script_path, 'r') as f:
                            f.read(1)
                    except Exception:
                        continue
                # Determinar el tipo de script y su descripción personalizada basada en el nombre del script
                script_base = os.path.splitext(script_name)[0]
                descriptions = {
                    # Scripts de mantenimiento
                    'supervise_gunicorn': 'Supervisa y reinicia automáticamente el servidor Gunicorn si deja de funcionar',
                    'supervise_gunicorn_web': 'Supervisa el servidor web Gunicorn con interfaz web de monitoreo',
                    'monitor_socket': 'Monitorea los sockets de red para detectar problemas de conexión',
                    'update': 'Actualiza el código de la aplicación desde el repositorio',
                    'iniciar_app_directo': 'Inicia la aplicación en modo directo sin Gunicorn',
                    'start_gunicorn': 'Inicia el servidor Gunicorn con la configuración óptima',
                    'setup_monitoring_cron': 'Configura tareas programadas para monitoreo del sistema',
                    'iniciar_produccion': 'Inicia la aplicación en modo producción con todas las optimizaciones',
                    'restart_server': 'Reinicia todos los servicios del servidor',
                    'daily_report': 'Genera un informe diario del estado del sistema',
                    
                    # Scripts de DB utils
                    'fix_mongodb_connection': 'Repara la conexión a MongoDB en caso de problemas',
                    'fix_mongodb_atlas': 'Configura o repara la conexión a MongoDB Atlas',
                    
                    # Scripts de admin utils
                    'cleanup_backups': 'Limpia archivos de respaldo antiguos conservando los más recientes',
                    'fix_script_permissions': 'Corrige permisos de ejecución en scripts del sistema',
                    
                    # Scripts para sesiones
                    'session_fix': 'Soluciona problemas con sesiones de usuario',
                    'session_config': 'Configura opciones avanzadas de sesiones',
                    
                    # Scripts de imágenes
                    'migrate_images_to_s3': 'Migra imágenes locales a almacenamiento S3',
                    'clean_images': 'Elimina imágenes no utilizadas para liberar espacio',
                    
                    # Scripts de monitoreo
                    'check_logs': 'Analiza logs del sistema en busca de errores',
                    'monitor_mongodb': 'Monitorea el rendimiento y disponibilidad de MongoDB'
                }
                if script_base in descriptions:
                    description = descriptions[script_base]
                elif script_ext == '.sh':
                    description = f"Script de shell para {category_info['name']}"
                else:  # .py
                    description = f"Script de Python para {category_info['name']}"
                rel_path = os.path.relpath(script_path, TOOLS_DIR)
                print(f"Añadiendo script: {script_path} (ruta relativa: {rel_path})")
                scripts.append({
                    'name': script_name,
                    'path': rel_path,
                    'category': category_id,
                    'description': description,
                    'full_path': script_path
                })
        else:
            print(f"Directorio no encontrado: {path}")
    print(f"Total de scripts encontrados: {len(scripts)}")
    if len(scripts) == 0:
        print("ADVERTENCIA: No se encontraron scripts para mostrar")
    return render_template('admin/tools_dashboard.html', scripts=scripts, categories=script_categories)

@scripts_bp.route('/run/<path:script_path>', methods=['POST'])
@admin_required
def run_script(script_path):
    """Ejecuta un script y devuelve su salida"""
    try:
        print(f"\n=== Iniciando ejecución de script ===")
        print(f"Script solicitado: {script_path}")
        print(f"URL completa: {request.url}")
        print(f"Método: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        
        # Obtener la ruta absoluta del script usando la función mejorada
        abs_script_path = get_script_path(script_path)
        print(f"Ruta absoluta del script: {abs_script_path}")
        
        if not abs_script_path:
            print(f"\n❌ ERROR: Script no encontrado: {script_path}")
            return jsonify({
                'error': f'Script no encontrado: {script_path}',
                'script': os.path.basename(script_path)
            }), 404
        
        # Verificar que el script está dentro del directorio del proyecto
        if not abs_script_path.startswith(ROOT_DIR):
            print(f"\n❌ ERROR: Script fuera del directorio del proyecto: {abs_script_path}")
            return jsonify({
                'error': 'Script fuera del directorio del proyecto: ' + abs_script_path,
                'script': os.path.basename(script_path)
            }), 404
    
        # Verificar que el script tiene permisos de ejecución
        if not os.access(abs_script_path, os.X_OK):
            try:
                # Intentar dar permisos de ejecución al archivo
                os.chmod(abs_script_path, 0o755)
                print(f"Permisos de ejecución establecidos para: {abs_script_path}")
            except Exception as e:
                print(f"\n❌ ERROR al establecer permisos: {str(e)}")
                return jsonify({
                    'error': f'No se pudieron establecer permisos de ejecución: {str(e)}',
                    'script': os.path.basename(script_path)
                }), 403
        
        # Determinar cómo ejecutar el script basado en su tipo
        script_ext = os.path.splitext(abs_script_path)[1].lower()
        
        try:
            cmd = None
            if script_ext == '.py':
                # Para scripts Python, usar el intérprete de Python directamente
                cmd = [sys.executable, abs_script_path]
            elif script_ext == '.sh':
                # Para scripts shell, usar bash
                cmd = ['/bin/bash', abs_script_path]
            else:
                # Para otros ejecutables
                cmd = [abs_script_path]
            
            print(f"\n✅ Ejecutando comando: {' '.join(cmd)}")
            
            # Ejecutar el script directamente
            result_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(abs_script_path)  # Establecer el directorio de trabajo al directorio del script
            )
            
            stdout = result_process.stdout
            stderr = result_process.stderr
            exit_code = result_process.returncode
            
            print(f"\n✅ Script ejecutado. Código de salida: {exit_code}")
            print(f"Salida estándar: {stdout[:100]}..." if len(stdout) > 100 else f"Salida estándar: {stdout}")
            print(f"Error estándar: {stderr[:100]}..." if len(stderr) > 100 else f"Error estándar: {stderr}")
            
            result = {
                'script': os.path.basename(script_path),
                'exit_code': exit_code,
                'output': stdout,
                'error': stderr,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return jsonify(result)
        except subprocess.TimeoutExpired:
            print(f"\n❌ Timeout al ejecutar el script: {abs_script_path}")
            return jsonify({
                'script': os.path.basename(script_path),
                'error': 'El script tardó demasiado tiempo en ejecutarse (más de 30 segundos)',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 408
    except Exception as e:
        print(f"\n❌ Excepción al ejecutar el script: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'script': os.path.basename(script_path),
            'error': f'Error al ejecutar el script: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500
