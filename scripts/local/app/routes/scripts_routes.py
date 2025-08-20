#!/usr/bin/env python3
# app/routes/scripts_routes.py

import os
import subprocess
import sys
import urllib.parse
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


# === Utilidad para extraer la descripción de scripts ===
def extract_description(script_path):
    """Extrae la descripción de un script desde sus comentarios."""
    try:
        with open(script_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Para scripts Python con comentarios tipo '# Descripción:'
                if line.startswith("# Descripción:"):
                    return line.replace("# Descripción:", "").strip()
                # Para scripts bash con comentarios tipo '# Descripción:'
                if line.startswith("#") and "Descripción:" in line:
                    return line.split("Descripción:")[1].strip()
                # Para scripts con descripción en la segunda línea (formato común)
                if line.startswith("# Script") and "para" in line:
                    return line.replace("# Script", "").strip()
                # Para scripts con descripción simple en comentario
                if line.startswith("#") and len(line) > 2 and not line.startswith("#!"):
                    # Buscar descripción después de "Script" o "para"
                    if "Script" in line and "para" in line:
                        parts = line.split("para")
                        if len(parts) > 1:
                            return parts[1].strip()
                    elif "para" in line:
                        parts = line.split("para")
                        if len(parts) > 1:
                            return parts[1].strip()
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error al extraer descripción de {script_path}: {e}")
    return ""


# Definición local del decorador admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in") or session.get("role") != "admin":
            flash("No tiene permisos para acceder a esta página", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


# Definir el directorio raíz
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

# Definir el directorio de herramientas donde se encuentran las copias de los scripts
tools_dir = os.path.join(ROOT_DIR, "tools")

# Crear el blueprint
scripts_bp = Blueprint("scripts", __name__, url_prefix="/admin/tools")


@scripts_bp.route("/api/scripts_metadata")
@admin_required
def scripts_metadata():
    """Devuelve un JSON con todos los scripts agrupados por entorno (local/producción) y categoría."""
    resultado = []

    # Definir categorías y sus directorios correspondientes para LOCAL
    categorias_local = {
        "Database Utils": ["tools/local/db_utils", "scripts/local/maintenance"],
        "System Maintenance": [
            "scripts/local/maintenance",
            "tools/local/maintenance",
            "tools/local/system",
        ],
        "User Management": [
            "tools/local/admin_utils",
            "tools/local/user_utils",
            "scripts/local/admin_utils",
        ],
        "File Management": [
            "tools/local/utils",
            "tools/local/catalog_utils",
        ],
        "Monitoring": ["tools/local/monitoring", "tools/local/diagnostico"],
        "Testing": [
            "tests/local/unit",
            "tests/local/integration",
            "tests/local/functional",
            "tests/local/performance",
            "tests/local/security",
        ],
        "Development Tools": [
            "tools/local/app",
            "tools/local/src",
            "scripts/local/app",
        ],
        "Infrastructure": ["tools/local/aws_utils", "tools/local/session_utils"],
        "Root Tools": ["tools/local/utils"],
    }

    # Definir categorías y sus directorios correspondientes para PRODUCCIÓN
    categorias_produccion = {
        "Database Utils": [
            "tools/production/db_utils",
            "scripts/production/maintenance",
        ],
        "System Maintenance": [
            "scripts/production/maintenance",
            "tools/production/maintenance",
            "tools/production/system",
        ],
        "User Management": [
            "tools/production/admin_utils",
            "tools/production/user_utils",
        ],
        "File Management": [
            "tools/production/utils",
            "tools/production/catalog_utils",
        ],
        "Monitoring": ["tools/production/monitoring", "tools/production/diagnostico"],
        "Testing": [
            "tests/production/unit",
            "tests/production/integration",
            "tests/production/functional",
            "tests/production/performance",
            "tests/production/security",
        ],
        "Development Tools": ["tools/production/app", "tools/production/src"],
        "Infrastructure": [
            "tools/production/aws_utils",
            "tools/production/session_utils",
        ],
        "Root Tools": ["tools/production/utils"],
    }

    # Procesar scripts LOCALES
    scripts_locales = []
    for categoria, directorios in categorias_local.items():
        scripts_categoria = []

        for directorio in directorios:
            dir_path = os.path.join(ROOT_DIR, directorio)
            if os.path.isdir(dir_path):
                try:
                    for fname in os.listdir(dir_path):
                        fpath = os.path.join(dir_path, fname)
                        # Solo incluir archivos, no directorios
                        if os.path.isfile(fpath) and (
                            fname.endswith(".py") or fname.endswith(".sh")
                        ):
                            descripcion = extract_description(fpath)
                            if not descripcion:
                                descripcion = "Sin descripción"

                            # Determinar si es ejecutable
                            executable = fname.endswith(".py") or os.access(
                                fpath, os.X_OK
                            )

                            scripts_categoria.append(
                                {
                                    "nombre": fname,
                                    "descripcion": descripcion,
                                    "path": os.path.join(directorio, fname),
                                    "executable": executable,
                                    "tipo": "python"
                                    if fname.endswith(".py")
                                    else "bash",
                                    "entorno": "local",
                                }
                            )
                except OSError as e:
                    print(f"Error procesando {directorio}: {e}")
                    continue

        if scripts_categoria:
            scripts_locales.append(
                {"categoria": categoria, "scripts": scripts_categoria}
            )

    # Procesar scripts de PRODUCCIÓN
    scripts_produccion = []
    for categoria, directorios in categorias_produccion.items():
        scripts_categoria = []

        for directorio in directorios:
            dir_path = os.path.join(ROOT_DIR, directorio)
            if os.path.isdir(dir_path):
                try:
                    for fname in os.listdir(dir_path):
                        fpath = os.path.join(dir_path, fname)
                        # Solo incluir archivos, no directorios
                        if os.path.isfile(fpath) and (
                            fname.endswith(".py") or fname.endswith(".sh")
                        ):
                            descripcion = extract_description(fpath)
                            if not descripcion:
                                descripcion = "Sin descripción"

                            # Determinar si es ejecutable
                            executable = fname.endswith(".py") or os.access(
                                fpath, os.X_OK
                            )

                            scripts_categoria.append(
                                {
                                    "nombre": fname,
                                    "descripcion": descripcion,
                                    "path": os.path.join(directorio, fname),
                                    "executable": executable,
                                    "tipo": "python"
                                    if fname.endswith(".py")
                                    else "bash",
                                    "entorno": "produccion",
                                }
                            )
                except OSError as e:
                    print(f"Error procesando {directorio}: {e}")
                    continue

        if scripts_categoria:
            scripts_produccion.append(
                {"categoria": categoria, "scripts": scripts_categoria}
            )

    # Organizar resultado por entorno
    resultado = {"local": scripts_locales, "produccion": scripts_produccion}

    return jsonify(resultado)


# Ruta alternativa para ejecutar scripts sin path variables
@scripts_bp.route("/execute", methods=["POST"])
@admin_required
def execute_script():
    """Ejecuta un script especificado por parámetro y devuelve su salida"""
    try:
        # Obtener la ruta del script desde los parámetros del formulario o JSON
        script_path = ""

        try:
            # Verificar el Content-Type del request
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                # Intentar parsear JSON solo si el Content-Type es correcto
                if request.is_json:
                    data = request.get_json()
                    if data and isinstance(data, dict):
                        # Compatibilidad: aceptar 'rel_path' o 'script_path'
                        script_path = (
                            data.get("rel_path") or data.get("script_path") or ""
                        )
                else:
                    print(
                        "Error: Content-Type indica JSON pero request no es JSON válido"
                    )
                    script_path = ""
            elif (
                "application/x-www-form-urlencoded" in content_type
                or "multipart/form-data" in content_type
            ):
                # Form data
                script_path = (
                    request.form.get("rel_path")
                    or request.form.get("script_path")
                    or ""
                )
            else:
                # Intentar ambos métodos como fallback
                try:
                    if request.is_json:
                        data = request.get_json()
                        if data and isinstance(data, dict):
                            script_path = (
                                data.get("rel_path") or data.get("script_path") or ""
                            )
                except:
                    pass

                if not script_path:
                    script_path = (
                        request.form.get("rel_path")
                        or request.form.get("script_path")
                        or ""
                    )
        except Exception as e:
            print(f"Error parsing request data: {e}")
            script_path = ""

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

    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        return jsonify(
            {
                "error": f"Error al ejecutar script: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ), 500


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
        os.path.join(ROOT_DIR, "tools", script_path),
        # En directorio scripts
        os.path.join(ROOT_DIR, "scripts", script_path),
    ]

    # Buscar en subdirectorios comunes
    for subdir in [
        "maintenance",
        "admin_utils",
        "backup",
        "monitoring",
        "security",
        "database",
        "app",
    ]:
        possible_paths.append(os.path.join(ROOT_DIR, "tools", subdir, script_path))
        possible_paths.append(os.path.join(ROOT_DIR, "scripts", subdir, script_path))
        possible_paths.append(
            os.path.join(ROOT_DIR, "scripts", "local", subdir, script_path)
        )

    # Verificar cada ruta posible
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
    """Devuelve el contenido de un script específico como JSON."""
    try:
        # Decodificar la ruta URL
        decoded_path = urllib.parse.unquote(script_path)

        abs_path = get_script_path(decoded_path)

        if not os.path.exists(abs_path):
            return jsonify({"error": f"Script no encontrado: {decoded_path}"}), 404

        # Verificar que está dentro del directorio del proyecto
        if not abs_path.startswith(ROOT_DIR):
            return jsonify(
                {"error": f"Script fuera del directorio del proyecto: {abs_path}"}
            ), 403

        with open(abs_path, encoding="utf-8") as f:
            content = f.read()

        return jsonify(
            {"content": content, "path": abs_path, "name": os.path.basename(abs_path)}
        )
    except Exception as e:
        return jsonify({"error": f"Error al leer el script: {str(e)}"}), 500


@scripts_bp.route("/")
@admin_required
def tools_dashboard():
    """Dashboard principal de herramientas."""
    return render_template("admin/tools_dashboard.html")


@scripts_bp.route("/run/<path:script_path>", methods=["POST"])
@admin_required
def run_script(script_path):
    """Ejecuta un script específico."""
    try:
        # Obtener el comando del request si existe
        command = ""

        # Verificar que el request es válido antes de procesarlo
        if not request or not hasattr(request, "headers"):
            print("Error: Request inválido o malformado")
            return jsonify(
                {"error": "Request inválido", "script": script_path, "status": "error"}
            ), 400

        try:
            # Verificar el Content-Type del request
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                # Intentar parsear JSON solo si el Content-Type es correcto
                if request.is_json:
                    data = request.get_json()
                    if data and isinstance(data, dict):
                        command = data.get("command", "").strip()
                else:
                    print(
                        "Error: Content-Type indica JSON pero request no es JSON válido"
                    )
                    command = ""
            elif (
                "application/x-www-form-urlencoded" in content_type
                or "multipart/form-data" in content_type
            ):
                # Form data
                command = request.form.get("command", "").strip()
            else:
                # Intentar ambos métodos como fallback
                try:
                    if request.is_json:
                        data = request.get_json()
                        if data and isinstance(data, dict):
                            command = data.get("command", "").strip()
                except Exception as json_error:
                    print(f"Error parseando JSON: {json_error}")
                    command = ""

                if not command:
                    try:
                        command = request.form.get("command", "").strip()
                    except Exception as form_error:
                        print(f"Error obteniendo form data: {form_error}")
                        command = ""

        except Exception as e:
            print(f"Error parsing request data: {e}")
            command = ""

        abs_script_path = get_script_path(script_path)

        if not os.path.exists(abs_script_path):
            return jsonify(
                {
                    "error": f"Script no encontrado: {script_path}",
                    "script": script_path,
                }
            ), 404

        # Verificar que está dentro del directorio del proyecto
        if not abs_script_path.startswith(ROOT_DIR):
            return jsonify(
                {
                    "error": f"Script fuera del directorio del proyecto: {abs_script_path}",
                    "script": script_path,
                }
            ), 403

        # Determinar el tipo de script y ejecutarlo
        script_name = os.path.basename(abs_script_path)
        script_ext = os.path.splitext(script_name)[1].lower()

        # Configurar el entorno de ejecución
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT_DIR

        if script_ext == ".py":
            # Script Python
            if command:
                cmd = [sys.executable, abs_script_path, command]
            else:
                cmd = [sys.executable, abs_script_path]
        elif script_ext == ".sh":
            # Script Bash
            if command:
                cmd = ["bash", abs_script_path, command]
            else:
                cmd = ["bash", abs_script_path]
        else:
            return jsonify(
                {
                    "error": f"Tipo de script no soportado: {script_ext}",
                    "script": script_path,
                }
            ), 400

        # Ejecutar el script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            env=env,
            timeout=300,  # 5 minutos de timeout
        )

        # Preparar la respuesta
        response = {
            "script": script_path,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": datetime.now().isoformat(),
            "command_used": command if command else None,
        }

        if result.returncode == 0:
            response["status"] = "success"
            response["message"] = f"Script ejecutado exitosamente: {script_name}"
        else:
            response["status"] = "error"
            response["message"] = (
                f"Script falló con código {result.returncode}: {script_name}"
            )

        return jsonify(response)

    except subprocess.TimeoutExpired:
        return jsonify(
            {
                "error": f"Script excedió el tiempo límite de ejecución: {script_path}",
                "script": script_path,
                "status": "timeout",
            }
        ), 408
    except Exception as e:
        print(f"Error general en run_script: {str(e)}")
        return jsonify(
            {
                "error": f"Error al ejecutar script: {str(e)}",
                "script": script_path,
                "status": "error",
            }
        ), 500
