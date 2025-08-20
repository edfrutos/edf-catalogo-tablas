#!/usr/bin/env python3
# app/routes/scripts_routes.py

import glob  # noqa: F401
import json  # noqa: F401
import os
import subprocess
import sys
from datetime import datetime
from functools import wraps  # noqa: F811  # pyright: ignore[reportDuplicateImport]

from flask import (
    Blueprint,
    abort,  # noqa: F401
    current_app,  # noqa: F401
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,  # noqa: F401
    session,
    url_for,
)


# === Utilidad para extraer la descripción de scripts ===
def extract_description(script_path):
    """
    Extrae la línea de descripción de la cabecera de un script (.py o .sh).
    Busca una línea que empiece por '# Descripción:' y devuelve el texto.
    Lee solo las primeras 10 líneas para evitar errores de iterador.
    """
    try:
        with open(script_path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 9:
                    break
                if line.strip().startswith("# Descripción:"):
                    return line.strip().replace("# Descripción:", "").strip()
                # Para scripts bash con comentarios tipo '# Descripción:'
                if line.strip().startswith("#") and "Descripción:" in line:
                    return line.strip().split("Descripción:")[1].strip()
    except Exception as e:
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


# Utilizamos la definición local del decorador admin_required

# Definir el directorio raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Definir el directorio de herramientas donde se encuentran las copias de los scripts
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

# Crear el blueprint
scripts_bp = Blueprint("scripts", __name__, url_prefix="/admin/tools")


@scripts_bp.route("/api/scripts_metadata")
@admin_required
def scripts_metadata():
    """
    Devuelve un JSON con todos los scripts agrupados por categoría, extrayendo la descripción de la cabecera.
    """
    import fnmatch
    import os

    TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
    resultado = []

    print(f"[scripts_metadata] Buscando scripts en: {TOOLS_DIR}")

    # Primero, agregar scripts del directorio raíz tools/
    scripts_root = []
    if os.path.isdir(TOOLS_DIR):
        print(f"[scripts_metadata] Procesando directorio raíz: {TOOLS_DIR}")
        for fname in os.listdir(TOOLS_DIR):
            if fnmatch.fnmatch(fname, "*.py") or fnmatch.fnmatch(fname, "*.sh"):
                script_path = os.path.join(TOOLS_DIR, fname)
                if os.path.isfile(
                    script_path
                ):  # Asegurar que es un archivo, no directorio
                    descripcion = extract_description(script_path)
                    if not descripcion:
                        descripcion = "Sin descripción"
                    scripts_root.append({"nombre": fname, "descripcion": descripcion})
                    print(f"[scripts_metadata] Script encontrado en raíz: {fname}")

        if scripts_root:
            resultado.append(
                {"categoria": "Scripts Principales", "scripts": scripts_root}
            )
            print(
                f"[scripts_metadata] {len(scripts_root)} scripts encontrados en directorio raíz"
            )

    # Luego, procesar subdirectorios
    CATEGORIES = ["admin_utils", "db_utils", "diagnostico", "maintenance"]

    for categoria in CATEGORIES:
        cat_dir = os.path.join(TOOLS_DIR, categoria)
        print(f"[scripts_metadata] Procesando categoría: {categoria} en {cat_dir}")

        if not os.path.isdir(cat_dir):
            print(f"[scripts_metadata] Directorio no existe: {cat_dir}")
            continue

        scripts = []
        try:
            for fname in os.listdir(cat_dir):
                if fnmatch.fnmatch(fname, "*.py") or fnmatch.fnmatch(fname, "*.sh"):
                    script_path = os.path.join(cat_dir, fname)
                    if os.path.isfile(script_path):  # Asegurar que es un archivo
                        descripcion = extract_description(script_path)
                        if not descripcion:
                            descripcion = "Sin descripción"
                        scripts.append({"nombre": fname, "descripcion": descripcion})
                        print(
                            f"[scripts_metadata] Script encontrado en {categoria}: {fname}"
                        )
        except Exception as e:
            print(f"[scripts_metadata] Error procesando {categoria}: {e}")
            continue

        if scripts:  # Solo agregar categorías que tienen scripts
            resultado.append({"categoria": categoria, "scripts": scripts})
            print(
                f"[scripts_metadata] {len(scripts)} scripts encontrados en {categoria}"
            )

    print(f"[scripts_metadata] Total de categorías con scripts: {len(resultado)}")

    # Si no se encontraron scripts en ninguna parte, devolver mensaje de debug
    if not resultado:
        print(
            f"[scripts_metadata] ¡ERROR! No se encontraron scripts en ninguna categoría"  # noqa: F541
        )
        print(
            f"[scripts_metadata] Verificando existencia de TOOLS_DIR: {os.path.exists(TOOLS_DIR)}"
        )
        if os.path.exists(TOOLS_DIR):
            print(
                f"[scripts_metadata] Contenido de TOOLS_DIR: {os.listdir(TOOLS_DIR)[:10]}..."
            )  # Primeros 10

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

        print(f"\n=== Iniciando ejecución de script (método alternativo) ===")  # noqa: F541
        print(f"Script solicitado (rel_path): {script_path}")
        abs_script_path = os.path.join(
            TOOLS_DIR if not os.path.isabs(script_path) else "", script_path
        )
        print(f"Ruta absoluta construida: {abs_script_path}")
        print(f"URL completa: {request.url}")
        print(f"Método: {request.method}")
        print(f"Headers: {dict(request.headers)}")

        # Obtener la ruta absoluta del script
        abs_script_path = get_script_path(script_path)
        print(f"Ruta absoluta del script: {abs_script_path}")

        if not abs_script_path:
            print(f"\n❌ ERROR: Script no encontrado: {script_path}")
            return jsonify(
                {
                    "script": os.path.basename(script_path)
                    if script_path
                    else "desconocido",
                    "error": f"Script no encontrado: {script_path}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ), 404

        # Verificar que el script existe y es ejecutable
        if not os.path.isfile(abs_script_path):
            print(f"\n❌ ERROR: No es un archivo regular: {abs_script_path}")
            return jsonify(
                {
                    "script": os.path.basename(abs_script_path),
                    "error": f"No es un archivo válido: {abs_script_path}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ), 400

        if not os.access(abs_script_path, os.X_OK):
            print(f"\n❌ ERROR: Script no ejecutable: {abs_script_path}")
            # Intentar corregir los permisos
            try:
                os.chmod(abs_script_path, 0o755)
                print(f"Permisos corregidos para: {abs_script_path}")
            except Exception as e:
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

            # Obtener la salida y el código de salida
            output = process.stdout
            error_output = process.stderr
            exit_code = process.returncode

            print(f"Código de salida: {exit_code}")
            print(f"Salida:\n{output}")

            if error_output:
                print(f"Error:\n{error_output}")

            # Devolver la respuesta en formato JSON
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
        print(f"\n❌ Excepción al ejecutar el script: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify(
            {
                "script": os.path.basename(script_path)
                if "script_path" in locals()
                else "desconocido",
                "error": f"Error al ejecutar el script: {str(e)}",
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

def     view_script_content(script_path):
    """Muestra el contenido de un script"""
    # Utilizar la función get_script_path para normalizar la ruta
    abs_script_path = get_script_path(script_path)

    print(f"Intentando acceder al script: {abs_script_path}")

    # Verificar que el script existe
    if not os.path.exists(abs_script_path):
        flash("Script no encontrado: " + abs_script_path, "error")
        return redirect(url_for("scripts.tools_dashboard"))

    # Verificar que el script está dentro del directorio del proyecto
    if not abs_script_path.startswith(ROOT_DIR):
        flash("Script fuera del directorio del proyecto: " + abs_script_path, "error")
        return redirect(url_for("scripts.tools_dashboard"))

    try:
        # Leer el contenido del script
        with open(abs_script_path) as f:
            script_content = f.read()

        return render_template(
            "script_content.html",
            script_name=os.path.basename(abs_script_path),
            script_path=abs_script_path,
            script_content=script_content,
        )
    except Exception as e:
        flash(f"Error al leer el contenido del script: {str(e)}", "error")
        return redirect(url_for("scripts.tools_dashboard"))


@scripts_bp.route("/")
@admin_required
def tools_dashboard():
    """Ruta para acceder al gestor de scripts del sistema (/admin/tools/) (muestra la plantilla, la lógica de scripts es vía JS/API)"""
    return render_template("admin/tools_dashboard.html")


@scripts_bp.route("/run/<path:script_path>", methods=["POST"])
@admin_required
@scripts_bp.route('/run/<path:script_path>', methods=['POST'])
@admin_required
@scripts_bp.route('/run/<path:script_path>', methods=['POST'])
@admin_required
@scripts_bp.route('/run/<path:script_path>', methods=['POST'])
@admin_required
@scripts_bp.route('/run/<path:script_path>', methods=['POST'])
@admin_required
def run_script(script_path):
    """Ejecuta un script y devuelve su salida"""
    try:
        print(f"\n=== Iniciando ejecución de script ===")  # noqa: F541
        print(f"Script solicitado: {script_path}")
        print(f"URL completa: {request.url}")
        print(f"Método: {request.method}")
        print(f"Headers: {dict(request.headers)}")

        # Obtener la ruta absoluta del script usando la función mejorada
        abs_script_path = get_script_path(script_path)
        print(f"Ruta absoluta del script: {abs_script_path}")

        if not abs_script_path:
            print(f"\n❌ ERROR: Script no encontrado: {script_path}")
            return jsonify(
                {
                    "error": f"Script no encontrado: {script_path}",
                    "script": os.path.basename(script_path),
                }
            ), 404

        # Verificar que el script está dentro del directorio del proyecto
        if not abs_script_path.startswith(ROOT_DIR):
            print(
                f"\n❌ ERROR: Script fuera del directorio del proyecto: {abs_script_path}"
            )
            return jsonify(
                {
                    "error": "Script fuera del directorio del proyecto: "
                    + abs_script_path,
                    "script": os.path.basename(script_path),
                }
            ), 404

        # Verificar que el script tiene permisos de ejecución
        if not os.access(abs_script_path, os.X_OK):
            try:
                # Intentar dar permisos de ejecución al archivo
                os.chmod(abs_script_path, 0o755)
                print(f"Permisos de ejecución establecidos para: {abs_script_path}")
            except Exception as e:
                print(f"\n❌ ERROR al establecer permisos: {str(e)}")
                return jsonify(
                    {
                        "error": f"No se pudieron establecer permisos de ejecución: {str(e)}",
                        "script": os.path.basename(script_path),
                    }
                ), 403

        # Determinar cómo ejecutar el script basado en su tipo
        script_ext = os.path.splitext(abs_script_path)[1].lower()

        try:
            cmd = None
            if script_ext == ".py":
                # Para scripts Python, usar el intérprete de Python directamente
                cmd = [sys.executable, abs_script_path]
            elif script_ext == ".sh":
                # Para scripts shell, usar bash
                cmd = ["/bin/bash", abs_script_path]
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
                cwd=os.path.dirname(
                    abs_script_path
                ),  # Establecer el directorio de trabajo al directorio del script
            )

            stdout = result_process.stdout
            stderr = result_process.stderr
            exit_code = result_process.returncode

            print(f"\n✅ Script ejecutado. Código de salida: {exit_code}")
            print(
                f"Salida estándar: {stdout[:100]}..."
                if len(stdout) > 100
                else f"Salida estándar: {stdout}"
            )
            print(
                f"Error estándar: {stderr[:100]}..."
                if len(stderr) > 100
                else f"Error estándar: {stderr}"
            )

            # Formato de salida legible en texto plano
            output_text = (
                f"=== Resultado de la ejecución ===\n"
                f"Script: {os.path.basename(script_path)}\n"
                f"Código de salida: {exit_code}\n"
                f"\n--- Salida estándar (stdout) ---\n"
                f"{stdout}\n"
                f"--- Fin de stdout ---\n"
                f"\n--- Salida de error (stderr) ---\n"
                f"{stderr}\n"
                f"--- Fin de stderr ---\n"
                f"\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            from flask import Response

            return Response(output_text, mimetype="text/plain")
        except subprocess.TimeoutExpired:
            print(f"\n❌ Timeout al ejecutar el script: {abs_script_path}")
            output_text = (
                f"ERROR: El script tardó demasiado tiempo en ejecutarse (más de 30 segundos)\n"
                f"Script: {os.path.basename(script_path)}\n"
                f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            from flask import Response

            return Response(output_text, mimetype="text/plain"), 408
    except Exception as e:
        print(f"\n❌ Excepción al ejecutar el script: {str(e)}")
        import traceback

        traceback.print_exc()
        from flask import Response

        output_text = (
            f"ERROR: Excepción al ejecutar el script: {str(e)}\n"
            f"Script: {os.path.basename(script_path)}\n"
            f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        return Response(output_text, mimetype="text/plain"), 500
