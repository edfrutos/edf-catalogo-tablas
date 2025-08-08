#!/usr/bin/env python3
# app/routes/testing_routes.py

import os
import subprocess
import sys
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

# Crear el blueprint
testing_bp = Blueprint("testing", __name__, url_prefix="/dev-template/testing")


@testing_bp.route("/")
@admin_required
def testing_dashboard():
    """Dashboard principal de testing."""
    return render_template("dev_template/testing/index.html")


@testing_bp.route("/api/tests_metadata")
@admin_required
def tests_metadata():
    """Devuelve un JSON con todos los tests organizados por entorno (local/producción) y categoría."""
    resultado = {}

    # Definir categorías de tests para LOCAL
    categorias_local = {
        "Unit Tests": ["tests/local/unit"],
        "Integration Tests": ["tests/local/integration"],
        "Functional Tests": ["tests/local/functional"],
        "Performance Tests": ["tests/local/performance"],
        "Security Tests": ["tests/local/security"],
    }

    # Definir categorías de tests para PRODUCCIÓN
    categorias_produccion = {
        "Unit Tests": ["tests/production/unit"],
        "Integration Tests": ["tests/production/integration"],
        "Functional Tests": ["tests/production/functional"],
        "Performance Tests": ["tests/production/performance"],
        "Security Tests": ["tests/production/security"],
    }

    # Procesar tests LOCALES
    tests_locales = []
    for categoria, directorios in categorias_local.items():
        tests_categoria = []

        for directorio in directorios:
            dir_path = os.path.join(ROOT_DIR, directorio)
            if os.path.isdir(dir_path):
                try:
                    for fname in os.listdir(dir_path):
                        fpath = os.path.join(dir_path, fname)
                        if (
                            os.path.isfile(fpath)
                            and fname.startswith("test_")
                            and fname.endswith(".py")
                        ):
                            descripcion = extract_test_description(fpath)
                            if not descripcion:
                                descripcion = "Test sin descripción"

                            tests_categoria.append(
                                {
                                    "nombre": fname,
                                    "descripcion": descripcion,
                                    "path": os.path.join(directorio, fname),
                                    "tipo": "pytest",
                                    "entorno": "local",
                                }
                            )
                except (IOError, OSError) as e:
                    print(f"Error procesando {directorio}: {e}")
                    continue

        if tests_categoria:
            tests_locales.append({"categoria": categoria, "tests": tests_categoria})

    # Procesar tests de PRODUCCIÓN
    tests_produccion = []
    for categoria, directorios in categorias_produccion.items():
        tests_categoria = []

        for directorio in directorios:
            dir_path = os.path.join(ROOT_DIR, directorio)
            if os.path.isdir(dir_path):
                try:
                    for fname in os.listdir(dir_path):
                        fpath = os.path.join(dir_path, fname)
                        if (
                            os.path.isfile(fpath)
                            and fname.startswith("test_")
                            and fname.endswith(".py")
                        ):
                            descripcion = extract_test_description(fpath)
                            if not descripcion:
                                descripcion = "Test sin descripción"

                            tests_categoria.append(
                                {
                                    "nombre": fname,
                                    "descripcion": descripcion,
                                    "path": os.path.join(directorio, fname),
                                    "tipo": "pytest",
                                    "entorno": "produccion",
                                }
                            )
                except (IOError, OSError) as e:
                    print(f"Error procesando {directorio}: {e}")
                    continue

        if tests_categoria:
            tests_produccion.append({"categoria": categoria, "tests": tests_categoria})

    # Organizar resultado por entorno
    resultado = {"local": tests_locales, "produccion": tests_produccion}

    return jsonify(resultado)


def extract_test_description(test_path):
    """Extrae la descripción de un test desde sus comentarios."""
    try:
        with open(test_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("# Descripción:"):
                    return line.strip().replace("# Descripción:", "").strip()
                if line.strip().startswith('"""') and "Descripción:" in line:
                    return line.strip().split("Descripción:")[1].split('"""')[0].strip()
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Error al extraer descripción de {test_path}: {e}")
    return ""


@testing_bp.route("/run/<path:test_path>", methods=["POST"])
@admin_required
def run_test(test_path):
    """Ejecuta un test específico."""
    try:
        abs_test_path = get_test_path(test_path)

        if not os.path.exists(abs_test_path):
            return jsonify(
                {
                    "error": f"Test no encontrado: {test_path}",
                    "test": test_path,
                }
            ), 404

        # Verificar que está dentro del directorio del proyecto
        if not abs_test_path.startswith(ROOT_DIR):
            return jsonify(
                {
                    "error": f"Test fuera del directorio del proyecto: {abs_test_path}",
                    "test": test_path,
                }
            ), 403

        # Configurar el entorno de ejecución
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT_DIR

        # Ejecutar el test con pytest
        cmd = [sys.executable, "-m", "pytest", abs_test_path, "-v", "--tb=short"]

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
            "test": test_path,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": datetime.now().isoformat(),
        }

        if result.returncode == 0:
            response["status"] = "success"
            response["message"] = (
                f"Test ejecutado exitosamente: {os.path.basename(abs_test_path)}"
            )
        else:
            response["status"] = "error"
            response["message"] = (
                f"Test falló con código {result.returncode}: {os.path.basename(abs_test_path)}"
            )

        return jsonify(response)

    except subprocess.TimeoutExpired:
        return jsonify(
            {
                "error": f"Test excedió el tiempo límite de ejecución: {test_path}",
                "test": test_path,
                "status": "timeout",
            }
        ), 408
    except Exception as e:
        return jsonify(
            {
                "error": f"Error al ejecutar test: {str(e)}",
                "test": test_path,
                "status": "error",
            }
        ), 500


def get_test_path(test_path):
    """Obtiene la ruta absoluta de un test."""
    # Si es una ruta absoluta dentro del proyecto, devolverla tal como está
    if os.path.isabs(test_path) and ROOT_DIR in test_path:
        return test_path

    # Si es una ruta absoluta pero fuera del proyecto, devolverla tal como está
    if os.path.isabs(test_path):
        return test_path

    # Buscar en directorios de tests
    possible_paths = [
        os.path.join(ROOT_DIR, test_path),
        os.path.join(ROOT_DIR, "tests", test_path),
        os.path.join(ROOT_DIR, "tests", "integration", test_path),
        os.path.join(ROOT_DIR, "tests", "app", "routes", test_path),
    ]

    # Buscar el primer archivo que exista
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Test encontrado en: {path}")
            return path

    # Si no se encuentra, devolver la ruta original
    print(f"Test no encontrado: {test_path}")
    return os.path.join(ROOT_DIR, test_path)


@testing_bp.route("/run-all", methods=["POST"])
@admin_required
def run_all_tests():
    """Ejecuta todos los tests del proyecto."""
    try:
        # Configurar el entorno de ejecución
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT_DIR

        # Ejecutar todos los tests
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            env=env,
            timeout=600,  # 10 minutos de timeout para todos los tests
        )

        # Preparar la respuesta
        response = {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": datetime.now().isoformat(),
        }

        if result.returncode == 0:
            response["status"] = "success"
            response["message"] = "Todos los tests ejecutados exitosamente"
        else:
            response["status"] = "error"
            response["message"] = (
                f"Algunos tests fallaron con código {result.returncode}"
            )

        return jsonify(response)

    except subprocess.TimeoutExpired:
        return jsonify(
            {
                "error": "Los tests excedieron el tiempo límite de ejecución",
                "status": "timeout",
            }
        ), 408
    except Exception as e:
        return jsonify(
            {"error": f"Error al ejecutar tests: {str(e)}", "status": "error"}
        ), 500
