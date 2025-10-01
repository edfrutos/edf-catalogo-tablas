# Script: dev_template.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 dev_template.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

import os
from functools import wraps

from flask import (  # noqa: F401
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    render_template_string,
    request,
    send_file,
    send_from_directory,
    session,
)


# Decorador robusto para restringir a admin (soporta Flask-Login y session)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging

        logger = logging.getLogger("admin_required")
        try:
            from flask_login import current_user

            flask_login_available = True
        except ImportError:
            flask_login_available = False
            current_user = None
        # 1. Flask-Login: usuario autenticado y admin
        if flask_login_available and current_user is not None:
            logger.debug(f"[admin_required] current_user: {current_user}")
            if hasattr(current_user, "is_authenticated") and hasattr(
                current_user, "is_admin"
            ):
                logger.debug(
                    f"[admin_required] is_authenticated: {current_user.is_authenticated}"
                )
                logger.debug(
                    f"[admin_required] is_admin: {getattr(current_user, 'is_admin', None)}"
                )
                if not current_user.is_authenticated or not current_user.is_admin:
                    logger.warning(
                        "[admin_required] Bloqueado por Flask-Login (no admin o no autenticado)"
                    )
                    return (
                        jsonify({"success": False, "error": "Solo administradores"}),
                        403,
                    )
        # 2. Fallback: session
        elif session.get("username") and session.get("role") == "admin":
            logger.debug(
                f"[admin_required] session: {dict(session)} (admin OK por session)"
            )
            pass  # acceso permitido
        else:
            logger.warning(f"[admin_required] Bloqueado por session: {dict(session)}")
            return jsonify({"success": False, "error": "Solo administradores"}), 403
        return f(*args, **kwargs)

    return decorated_function


# Registro de Blueprint
bp_dev_template = Blueprint("dev_template", __name__, url_prefix="/dev-template")

README_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../templates/dev_template/README.md")
)


@bp_dev_template.route("/readme")
def show_readme():
    # ... (igual que antes)
    if not os.path.isfile(README_PATH):
        abort(404)
    with open(README_PATH, encoding="utf-8") as f:
        markdown_content = f.read()
    try:
        import markdown  # type: ignore

        html = markdown.markdown(markdown_content, extensions=["fenced_code", "tables"])
    except ImportError:
        html = "<pre>" + markdown_content + "</pre>"
    return render_template_string(
        """
    <!--<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Plantilla Desarrollo</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
        <style>body {background:#f8f9fa;} .container {max-width: 900px; margin-top: 2em;}</style>
    </head>
    <body>-->
    {% extends 'admin/base.html' %}

{% block title %}Plantilla Desarrollo{% endblock %}

{% block content %}
<a href="/admin" class="btn btn-link mt-3"><i class="bi bi-arrow-left"></i> Volver al panel</a>
      <div class="container">
        <h1 class="mb-4">Plantilla de Desarrollo</h1>
        <div class="card p-4 mb-3">
          <a href="/dev-template/readme/download" class="btn btn-outline-secondary btn-sm float-end">Descargar README.md</a>
          <span class="badge bg-info text-dark">Vista Markdown</span>
        </div>
        <div class="card card-body">
          {{ html|safe }}
        </div>
        <a href="/admin" class="btn btn-link mt-3"><i class="bi bi-arrow-left"></i> Volver al panel</a>
      </div>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
      {% endblock %}
    """,
        html=html,
    )


import subprocess  # noqa: E402
import threading  # noqa: E402

TESTS_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..//dev_template//tests")
)
INTEGRATION_DIR = os.path.join(TESTS_BASE, "integration")
APP_ROUTES_DIR = os.path.join(TESTS_BASE, "app", "routes")
PYTEST_REPORT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..//dev_template/pytest_report.html")
)

_test_lock = threading.Lock()


@bp_dev_template.route("/api/update-tests-readme", methods=["POST"])
@admin_required
def update_tests_readme():
    """
    Escanea los tests y actualiza la sección autogenerada del README.
    Incluye respaldo automático y mejor manejo de errores.
    """
    import re
    import shutil
    from datetime import datetime

    TESTS_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..//dev_template/tests")
    )
    README_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../templates/dev_template/README.md")
    )
    START = "<!-- TESTS-AUTO-START -->"
    END = "<!-- TESTS-AUTO-END -->"

    # Crear respaldo del README antes de modificarlo
    backup_path = f"{README_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Función mejorada para extraer documentación
    def extract_enhanced_description(script_path):
        """Extrae descripción mejorada de un script Python."""
        try:
            with open(script_path, encoding="utf-8") as sf:
                lines = sf.readlines()

            # Buscar docstring de módulo
            for i, line in enumerate(lines[:20]):  # Buscar en las primeras 20 líneas
                line = line.strip()

                # Docstring de módulo (""" o ''')
                if line.startswith('"""') or line.startswith("'''"):
                    # Docstring en una línea
                    if line.endswith('"""') or line.endswith("'''"):
                        desc = line.strip("\"'")
                        if desc and len(desc) > 5:  # Evitar docstrings vacíos
                            return desc
                    # Docstring multilínea
                    else:
                        desc_lines = [line.strip("\"'")]
                        for j in range(i + 1, min(i + 10, len(lines))):
                            next_line = lines[j].strip()
                            if next_line.endswith('"""') or next_line.endswith("'''"):
                                desc_lines.append(next_line.strip("\"'"))
                                break
                            desc_lines.append(next_line)
                        desc = " ".join(desc_lines).strip()
                        if desc and len(desc) > 5:
                            return desc

                # Comentarios de descripción
                if line.startswith("# Descripción:") or line.startswith("# Script:"):
                    return (
                        line.replace("# Descripción:", "")
                        .replace("# Script:", "")
                        .strip()
                    )

                # Comentarios generales (solo si son descriptivos)
                if (
                    line.startswith("#")
                    and len(line) > 10
                    and not line.startswith("#!")
                ):
                    comment = line.lstrip("#").strip()
                    if not any(
                        keyword in comment.lower()
                        for keyword in ["import", "coding", "author", "date"]
                    ):
                        return comment

        except Exception as e:
            print(f"Error extrayendo descripción de {script_path}: {e}")

        return ""

    # Generar tabla mejorada
    table_lines = []
    table_lines.append("| Ruta | Descripción | Tipo | Última Modificación |")
    table_lines.append("|------|-------------|------|---------------------|")

    test_count = 0
    for root, dirs, files in os.walk(TESTS_DIR):
        rel_dir = os.path.relpath(root, TESTS_DIR)
        for f in sorted(files):
            if f.endswith(".py") and not f.startswith("__"):
                script_path = os.path.join(root, f)
                rel_path = (
                    os.path.normpath(os.path.join(rel_dir, f)) if rel_dir != "." else f
                )

                # Extraer descripción mejorada
                desc = extract_enhanced_description(script_path)
                if not desc:
                    desc = "Script de testing sin documentación"

                # Obtener información del archivo
                try:
                    stat = os.stat(script_path)
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                except BaseException:
                    mod_time = "N/A"

                # Determinar tipo de test
                test_type = "Test"
                if "integration" in rel_path.lower():
                    test_type = "Integration"
                elif "unit" in rel_path.lower():
                    test_type = "Unit"
                elif "e2e" in rel_path.lower() or "end_to_end" in rel_path.lower():
                    test_type = "E2E"

                table_lines.append(
                    f"| `{rel_path}` | {desc} | {test_type} | {mod_time} |"
                )
                test_count += 1
    table = "\n".join(table_lines)
    import logging

    logger = logging.getLogger("update_tests_readme")

    try:
        # Verificar que el directorio de tests existe
        if not os.path.exists(TESTS_DIR):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Directorio de tests no encontrado: {TESTS_DIR}",
                    }
                ),
                404,
            )

        # Verificar que el README existe
        if not os.path.exists(README_PATH):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"README.md no encontrado: {README_PATH}",
                    }
                ),
                404,
            )

        # Crear respaldo del README
        try:
            shutil.copy2(README_PATH, backup_path)
            logger.info(f"[update-tests-readme] Respaldo creado: {backup_path}")
        except Exception as backup_error:
            logger.warning(
                f"[update-tests-readme] No se pudo crear respaldo: {backup_error}"
            )

        # Leer contenido actual
        with open(README_PATH, encoding="utf-8") as f:
            content = f.read()

        logger.info(
            f"[update-tests-readme] README.md leído correctamente: {README_PATH}"
        )

        # Crear nueva sección con estadísticas
        stats_section = f"""
## 📊 Estadísticas de Tests
- **Total de tests encontrados**: {test_count}
- **Última actualización**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Directorio escaneado**: `{os.path.basename(TESTS_DIR)}`

## 📋 Lista de Tests
"""

        new_section = f"{START}\n{stats_section}\n{table}\n{END}"

        # Verificar que ambos delimitadores existen
        if START not in content or END not in content:
            logger.error(
                f"[update-tests-readme] Delimitadores no encontrados en README. START: {START in content}, END: {END in content}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se encontraron los delimitadores de sección automática en README.md. Asegúrate de que existan los comentarios: <!-- TESTS-AUTO-START --> y <!-- TESTS-AUTO-END -->",
                        "missing_delimiters": {
                            "start": START not in content,
                            "end": END not in content,
                        },
                    }
                ),
                400,
            )

        # Reemplazo seguro
        updated, n = re.subn(f"{START}.*?{END}", new_section, content, flags=re.DOTALL)
        if n == 0:
            logger.error(
                "[update-tests-readme] El bloque delimitado no fue reemplazado. ¿Delimitadores corruptos?"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo reemplazar el bloque delimitado en README.md. Verifica que los delimitadores estén correctamente formateados.",
                    }
                ),
                400,
            )

        # Escribir archivo actualizado
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)

        logger.info(
            f"[update-tests-readme] README.md actualizado correctamente. Tests procesados: {test_count}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"README de tests actualizado correctamente. {test_count} tests procesados.",
                "stats": {
                    "tests_found": test_count,
                    "backup_created": os.path.exists(backup_path),
                    "backup_path": backup_path if os.path.exists(backup_path) else None,
                    "last_updated": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        logger.exception(f"[update-tests-readme] Error inesperado: {str(e)}")

        # Intentar restaurar desde respaldo si existe
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, README_PATH)
                logger.info(
                    f"[update-tests-readme] README restaurado desde respaldo: {backup_path}"
                )
            except Exception as restore_error:
                logger.error(
                    f"[update-tests-readme] Error restaurando desde respaldo: {restore_error}"
                )

        return jsonify(
            {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "backup_available": os.path.exists(backup_path),
                "backup_path": backup_path if os.path.exists(backup_path) else None,
            }
        )


@bp_dev_template.route("/api/script-params-help", methods=["POST"])
@admin_required
def script_params_help():
    """
    Devuelve la ayuda de parámetros de un script de test.
    - Si usa argparse/click, muestra la ayuda de --help.
    - Si no, lista las funciones test_* y sus argumentos.
    """
    import ast
    import re  # noqa: F401
    import subprocess

    data = request.get_json(force=True)
    rel_path = data.get("script_path", "").strip()
    if not rel_path:
        return jsonify({"success": False, "error": "Falta script_path"}), 400
    script_abs = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..//dev_template/tests", rel_path)
    )
    TESTS_BASE = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..//dev_template/tests")
    )
    if not script_abs.startswith(TESTS_BASE) or not os.path.isfile(script_abs):
        return jsonify({"success": False, "error": "Ruta de script no permitida"}), 400
    # Leer el código fuente
    try:
        with open(script_abs, encoding="utf-8") as f:
            code = f.read()
    except Exception:
        return jsonify({"success": False, "error": "No se pudo leer el script."})
    # Detectar si usa argparse o click
    uses_argparse = "import argparse" in code or "from argparse" in code
    uses_click = "import click" in code or "from click" in code
    # Listar funciones test_*
    test_funcs = []
    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                args = [a.arg for a in node.args.args]
                test_funcs.append({"name": node.name, "args": args})
    except Exception:
        pass
    # Si no usa argparse/click, mostrar mensaje y lista de funciones
    if not uses_argparse and not uses_click:
        msg = "Este test no acepta parámetros propios vía línea de comandos.\n"
        if test_funcs:
            msg += "Funciones de test disponibles en este archivo:\n"
            for f in test_funcs:
                msg += f"- {f['name']}({', '.join(f['args'])})\n"
            msg += "\nPuedes parametrizar estos tests modificando el código o usando pytest desde la CLI."
        else:
            msg += "No se detectaron funciones test_* en este archivo."
        return jsonify({"success": True, "help": msg.strip()})
    # Si usa argparse/click, intentar extraer la ayuda
    ayuda = ""
    try:
        proc = subprocess.run(
            ["python3", script_abs, "--help"], capture_output=True, text=True, timeout=4
        )
        salida = proc.stdout.strip() + (
            ("\n" + proc.stderr.strip()) if proc.stderr else ""
        )
        # Detectar si la salida es la ayuda de pytest (reconocer por patrón)
        if "pytest" in salida.lower() or "usage: pytest" in salida.lower():
            salida = "(Este script es un test de pytest: los parámetros de pytest deben usarse desde la CLI, no desde aquí.)"
        ayuda = salida
    except Exception as e:
        ayuda = f"(No se pudo obtener ayuda: {e})"
    return jsonify({"success": True, "help": ayuda or "(sin ayuda disponible)"})

    # @bp_dev_template.route("/testing")


# def testing():
#     import os
#
#     test_dirs = {}
#     base_dir = "/Users/edefrutos/_Repositorios/01.IDE_Cursor/edf_catalogotablas//dev_template/tests"
#     for root, dirs, files in os.walk(base_dir):
#         rel_dir = os.path.relpath(root, base_dir)
#         if rel_dir == ".":
#             rel_dir = "varios"
#         scripts_info = []
#         for f in files:
#             if f.endswith(".py") and not f.startswith("__"):
#                 script_path = os.path.join(root, f)
#                 desc = ""
#                 try:
#                     with open(script_path, "r", encoding="utf-8") as sf:
#                         lines = []
#                         for _ in range(10):
#                             line = sf.readline()
#                             if not line:
#                                 break
#                             lines.append(line.strip())
#                         desc = ""
#                         for l in lines:  # noqa: E741
#                             if not l or l.startswith("#!") or "coding" in l:
#                                 continue  # Ignorar shebang, encoding y vacías
#                             if l.startswith('"""') or l.startswith("'''"):
#                                 desc = l.strip("\"'")
#                                 break
#                             if l.startswith("#"):
#                                 desc = l.lstrip("#").strip()
#                                 break
#                 except Exception:
#                     desc = ""
#                 scripts_info.append(
#                     {
#                         "name": f,
#                         "desc": desc,
#                         "path": (rel_dir + "/" + f) if rel_dir != "varios" else f,
#                     }
#                 )
#         if scripts_info:
#             test_dirs[rel_dir] = scripts_info
#     return render_template("dev_template_testing.html", test_dirs=test_dirs)


@bp_dev_template.route("/generate-test-template", methods=["POST"])
def generate_test_template():
    import re

    data = request.get_json()
    name = (data or {}).get("name", "").strip()
    if not name:
        return (
            jsonify(success=False, error="Falta el nombre del modelo o endpoint."),
            400,
        )
    code = ""
    if name.startswith("/"):
        # Asume endpoint REST
        endpoint = name
        code = f"""import pytest\n\ndef test_{re.sub(r"[^a-zA-Z0-9]", "_", endpoint.strip("/"))}_get(client):\n    \"\"\"GET {endpoint} debe responder 200 o 401/403 si requiere auth.\"\"\"\n    resp = client.get('{endpoint}')\n    assert resp.status_code in (200, 401, 403)\n\ndef test_{re.sub(r"[^a-zA-Z0-9]", "_", endpoint.strip("/"))}_post(client):\n    \"\"\"POST {endpoint} (ajusta payload según tu API).\"\"\"\n    payload = {{}}\n    resp = client.post('{endpoint}', json=payload)\n    assert resp.status_code in (200, 201, 400, 401, 403)\n"""
    else:
        # Asume modelo/colección
        model = name
        code = f"""import pytest\n\n@pytest.fixture\ndef {model}_test(mongo_client_ssl):\n    \"\"\"Crea y elimina un {model} de prueba.\"\"\"\n    db = mongo_client_ssl.get_database()\n    doc = {{'nombre': 'test_{model}'}}\n    inserted = db.{model}.insert_one(doc)\n    yield doc\n    db.{model}.delete_one({{'_id': inserted.inserted_id}})\n\ndef test_{model}_crud(client, {model}_test):\n    \"\"\"CRUD básico para {model}.\"\"\"\n    # GET all\n    resp = client.get('/api/{model}/list')\n    assert resp.status_code in (200, 401, 403)\n    # POST crear\n    resp = client.post('/api/{model}/create', json={model}_test)\n    assert resp.status_code in (201, 400, 401, 403)\n"""
    return jsonify(success=True, code=code)

    # Construir test_tree: {subdir: {tests: [..], readme: bool}}
    test_tree = {}
    tests_root = TESTS_BASE
    for sub in os.listdir(tests_root):
        subdir_path = os.path.join(tests_root, sub)
        if os.path.isdir(subdir_path) and not sub.startswith("__"):
            tests = []
            readme = False
            for f in os.listdir(subdir_path):
                if f.lower() == "readme.md":
                    readme = True
                elif f.startswith("test_") and f.endswith(".py"):
                    tests.append(f)
            tests.sort()
            if tests or readme:
                test_tree[sub] = {"tests": tests, "readme": readme}
    return render_template("dev_template_testing.html", test_tree=test_tree)


@bp_dev_template.route("/run-test", methods=["POST"])
def run_test():
    """
    Ejecuta un test individual o todos, acepta parámetros adicionales. Devuelve el resultado en texto plano.
    """
    if not _test_lock.acquire(blocking=False):
        return jsonify(
            {"result": "Ya hay una ejecución de tests en curso. Espera a que termine."}
        )
    try:
        data = request.get_json(force=True)
        test_file = (data.get("test_file") or "").strip()
        params = data.get("params", "").strip()
        base_cmd = ["pytest", "--maxfail=5", "--disable-warnings", "-q", "--tb=short"]
        if params:
            base_cmd += params.split()
        # Añadir reporte HTML solo si es ejecución global
        if not test_file:
            base_cmd.append(TESTS_BASE)
        else:
            abs_path = os.path.join(TESTS_BASE, test_file)
            if not abs_path.startswith(TESTS_BASE) or not os.path.isfile(abs_path):
                return jsonify({"result": "Archivo de test no permitido."})
            base_cmd.append(abs_path)
        proc = subprocess.run(base_cmd, capture_output=True, text=True, timeout=120)
        output = proc.stdout + "\n" + proc.stderr
        return jsonify({"result": output})
    except Exception as e:
        return jsonify({"result": f"Error ejecutando test: {e}"})
    finally:
        _test_lock.release()


@bp_dev_template.route("/report")
def download_report():
    if not os.path.isfile(PYTEST_REPORT):
        return "No hay reporte generado. Ejecuta primero los tests.", 404
    return send_from_directory(
        os.path.dirname(PYTEST_REPORT),
        os.path.basename(PYTEST_REPORT),
        as_attachment=True,
    )


@bp_dev_template.route("/readme/download")
def download_readme():
    if not os.path.isfile(README_PATH):
        abort(404)
    return send_file(README_PATH, as_attachment=True)
