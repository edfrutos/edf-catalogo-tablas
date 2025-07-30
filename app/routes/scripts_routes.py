#!/usr/bin/env python3
# app/routes/scripts_routes.py

import os
import subprocess
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    flash,
)

# === Utilidad para extraer la descripción de scripts ===
def extract_description(script_path):
    """Extrae la descripción de un script desde sus comentarios."""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Para scripts Python con comentarios tipo '# Descripción:'
                if line.strip().startswith("# Descripción:"):
                    return line.strip().replace("# Descripción:", "").strip()
                # Para scripts bash con comentarios tipo '# Descripción:'
                if line.strip().startswith("#") and "Descripción:" in line:
                    return line.strip().split("Descripción:")[1].strip()
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Error al extraer descripción de {script_path}: {e}")
    return ""


# Definición local del decorador admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") != "admin":
            flash("No tiene permisos para acceder a esta página", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# Definir el directorio raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Definir el directorio de herramientas donde se encuentran las copias de los scripts
tools_dir = os.path.join(ROOT_DIR, "tools")

# Crear el blueprint
scripts_bp = Blueprint("scripts", __name__, url_prefix="/admin/tools")


@scripts_bp.route("/api/scripts_metadata")
@admin_required
def scripts_metadata():
    """Devuelve un JSON con todos los scripts agrupados por categoría."""
    tools_dir_local = os.path.join(ROOT_DIR, "tools")
    resultado = []

    print(f"[scripts_metadata] Buscando scripts en: {tools_dir_local}")

    # Primero, agregar scripts del directorio raíz tools/
    scripts_root = []
    if os.path.isdir(tools_dir):
        for fname in os.listdir(tools_dir):
            fpath = os.path.join(tools_dir, fname)
            if os.path.isfile(fpath) and (fname.endswith('.py') or fname.endswith('.sh')):
                descripcion = extract_description(fpath)
                if not descripcion:
                    descripcion = "Sin descripción"
                scripts_root.append({"nombre": fname, "descripcion": descripcion})

    if scripts_root:
        resultado.append({"categoria": "Scripts Raíz", "scripts": scripts_root})

    # Luego, buscar en subdirectorios
    for item in os.listdir(tools_dir):
        item_path = os.path.join(tools_dir, item)
        if os.path.isdir(item_path):
            scripts = []
            try:
                for fname in os.listdir(item_path):
                    fpath = os.path.join(item_path, fname)
                    if os.path.isfile(fpath) and (fname.endswith('.py') or fname.endswith('.sh')):
                        descripcion = extract_description(fpath)
                        if not descripcion:
                            descripcion = "Sin descripción"
                        scripts.append({"nombre": fname, "descripcion": descripcion})
            except (IOError, OSError) as e:
                print(f"[scripts_metadata] Error procesando {item}: {e}")
                continue

            if scripts:  # Solo agregar categorías que tienen scripts
                # Formatear el nombre de la categoría
                categoria_nombre = item.replace('_', ' ').title()
                resultado.append({"categoria": categoria_nombre, "scripts": scripts})

    return jsonify(resultado)


# Ruta alternativa para ejecutar scripts sin path variables
@scripts_bp.route("/execute", methods=["POST"])
@admin_required
def execute_script():
    """Ejecuta un script especificado por parámetro y devuelve su salida"""
    try:
        # Obtener la ruta del script desde los parámetros del formulario o JSON
        if request.is_json:
            data = request.get_json()
            # Compatibilidad: aceptar 'rel_path' o 'script_path'
            script_path = data.get("rel_path") or data.get("script_path") or ""
        else:
            script_path = (
                request.form.get("rel_path") or request.form.get("script_path") or ""
            )

        # Validación estricta: solo rutas relativas, sin '..' ni barra inicial
        if not script_path or ".." in script_path or script_path.startswith("/"):
            print(f"[execute_script] Rechazado script_path no permitido: {script_path}")
            return jsonify(
                {
                    "error": "Ruta no permitida (solo rutas relativas sin barra inicial)",
                    "script": script_path,
                }
            ), 400

        print("\n=== Iniciando ejecución de script (método alternativo) ===")
        print(f"Script solicitado (rel_path): {script_path}")
        abs_script_path = os.path.join(
            tools_dir if not os.path.isabs(script_path) else "", script_path
        )
        print(f"Ruta absoluta construida: {abs_script_path}")
        print(f"URL completa: {request.url}")
        print(f"Método: {request.method}")
        print(f"Headers: {dict(request.headers)}")

        # Verificar que el archivo existe
        if not os.path.exists(abs_script_path):
            print(f"[execute_script] Script no encontrado: {abs_script_path}")
            return jsonify(
                {
                    "error": f"Script no encontrado: {script_path}",
                    "script": script_path,
                }
            ), 404

        # Verificar que el archivo es ejecutable
        if not os.access(abs_script_path, os.X_OK):
            # Intentar corregir los permisos
            try:
                os.chmod(abs_script_path, 0o755)
                print(f"Permisos corregidos para: {abs_script_path}")
            except (OSError, PermissionError) as e:
                print(f"No se pudieron corregir los permisos: {str(e)}")
                return jsonify(
                    {
                        "script": os.path.basename(abs_script_path),
                        "error": f"Script no tiene permisos de ejecución: {abs_script_path}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ), 403

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
                check=False,  # No levantar excepción si el comando falla
            )

            # Obtener los resultados
            output = process.stdout
            error_output = process.stderr
            exit_code = process.returncode

            print(f"Código de salida: {exit_code}")
            print(f"Salida:\n{output}")

            if error_output:
                print(f"Error:\n{error_output}")

            # Devolver la respuesta JSON
            return jsonify(
                {
                    "script": os.path.basename(abs_script_path),
                    "output": output,
                    "error": error_output,
                    "exit_code": exit_code,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        except subprocess.TimeoutExpired:
            print(
                f"\n❌ ERROR: Tiempo de ejecución excedido ({timeout}s): {abs_script_path}"
            )
            return jsonify(
                {
                    "script": os.path.basename(abs_script_path),
                    "error": f"Tiempo de ejecución excedido ({timeout}s)",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ), 408

    except (IOError, OSError, subprocess.SubprocessError,
            FileNotFoundError, PermissionError) as e:
        return jsonify(
            {
                "error": f"Error al ejecutar script: {str(e)}",
                "script": script_path,
            }
        ), 500


def get_script_path(script_path):
    """Resuelve la ruta completa de un script."""
    # Si ya es una ruta absoluta y está dentro del directorio del proyecto
    if os.path.isabs(script_path) and ROOT_DIR in script_path:
        return script_path

    # Si es una ruta absoluta pero fuera del proyecto, devolverla tal como está
    if os.path.isabs(script_path):
        return script_path

    # Buscar en varios directorios posibles
    possible_paths = [
        # Ruta directa desde ROOT_DIR
        os.path.join(ROOT_DIR, script_path),
        # Dentro del directorio tools
        os.path.join(ROOT_DIR, 'tools', script_path),
        # Dentro del directorio scripts
        os.path.join(ROOT_DIR, 'scripts', script_path),
    ]

    # Agregar subdirectorios comunes
    for subdir in ['maintenance', 'admin_utils', 'backup', 'monitoring', 'security', 'database']:
        possible_paths.append(os.path.join(ROOT_DIR, 'tools', subdir, script_path))
        possible_paths.append(os.path.join(ROOT_DIR, 'scripts', subdir, script_path))

    # Buscar el primer archivo que exista
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Script encontrado en: {path}")
            return path

    # Si no se encuentra, devolver la ruta original
    print(f"Script no encontrado: {script_path}")
    return os.path.join(ROOT_DIR, script_path)


@scripts_bp.route("/content/<path:script_path>")
@admin_required
def view_script_content_route(script_path):
    """Muestra el contenido de un script específico."""
    try:
        # Decodificar la ruta URL
        import urllib.parse
        decoded_path = urllib.parse.unquote(script_path)
        
        abs_path = get_script_path(decoded_path)
        
        if not os.path.exists(abs_path):
            flash(f"Script no encontrado: {decoded_path}", "error")
            return redirect(url_for("scripts.tools_dashboard"))
        
        # Verificar que está dentro del directorio del proyecto
        if not abs_path.startswith(ROOT_DIR):
            flash(f"Script fuera del directorio del proyecto: {abs_path}", "error")
            return redirect(url_for("scripts.tools_dashboard"))
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return render_template(
            "admin/script_content.html",
            script_name=os.path.basename(abs_path),
            script_path=abs_path,
            script_content=content,
        )
    except Exception as e:
        flash(f"Error al leer el script: {str(e)}", "error")
        return redirect(url_for("scripts.tools_dashboard"))


@scripts_bp.route("/")
@admin_required
def tools_dashboard():
    """Dashboard principal de herramientas."""
    return render_template("admin/scripts_tools_overview.html")


@scripts_bp.route("/run/<path:script_path>", methods=["POST"])
@admin_required
def run_script(script_path):
    """Ejecuta un script específico."""
    try:
        abs_script_path = get_script_path(script_path)

        if not os.path.exists(abs_script_path):
            return jsonify(
                {
                    "error": f"Script no encontrado: {script_path}",
                    "script": script_path,
                }
            ), 404

        # Resto de la lógica de ejecución...
        # (Similar a execute_script pero usando script_path del URL)

    except Exception as e:
        return jsonify(
            {
                "error": f"Error al ejecutar script: {str(e)}",
                "script": script_path,
            }
        ), 500
