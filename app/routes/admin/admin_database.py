# Script: admin_database.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_database.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Database management routes for admin functionality.
"""
import logging
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.audit import audit_log
from app.database import get_mongo_client, get_mongo_db
from app.decorators import admin_required

admin_database_bp = Blueprint('admin_database', __name__, url_prefix='/admin/db')
logger = logging.getLogger(__name__)

@admin_database_bp.route("/status")
@admin_required
def db_status():
    """
    Muestra el estado de la conexión a MongoDB.
    """
    client = get_mongo_client()
    status = {
        "is_connected": False,
        "error": None,
        "databases": [],
        "collections": [],
        "server_info": None,
        "server_status": {},
    }

    try:
        if client is None:
            status["error"] = "Cliente MongoDB no disponible"
            return render_template("admin/db_status.html", status=status)

        # Probar conexión
        client.admin.command("ping")
        status["is_connected"] = True

        # Obtener información de la base de datos
        status["databases"] = client.list_database_names()

        # Obtener colecciones de la base de datos actual
        db = get_mongo_db()
        if db is not None:
            try:
                status["collections"] = db.list_collection_names()
            except Exception as e:
                logger.error("Error al obtener colecciones: %s", str(e))
                status["collections"] = []
                status["error"] = f"Error al obtener colecciones: {str(e)}"

        # Obtener información del servidor
        server_info = client.server_info()
        status["server_info"] = server_info

        # Obtener estadísticas del servidor
        try:
            server_status = client.admin.command("serverStatus")
            status["server_status"] = server_status
        except Exception as e:
            status["server_status"] = {
                "error": f"No se pudo obtener el estado del servidor: {str(e)}"
            }

    except Exception as e:
        status["error"] = f"Error al conectar con MongoDB: {str(e)}"
        logger.error(
            "Error en db_status: %s\n%s",
            str(e),
            traceback.format_exc()
        )

    return render_template("admin/db_status.html", status=status)

@admin_database_bp.route("/monitor")
@admin_required
def db_monitor():
    """
    Página de monitoreo en tiempo real de la base de datos.
    """
    client = get_mongo_client()
    status = {"is_connected": False, "error": None, "stats": {}, "server_status": {}}

    try:
        if client is None:
            status["error"] = "Cliente MongoDB no disponible"
            return render_template("admin/db_monitor.html", status=status)

        # Verificar conexión
        client.admin.command("ping")
        status["is_connected"] = True

        # Obtener estadísticas básicas
        db = get_mongo_db()
        if db is not None:
            try:
                status["stats"] = db.command("dbstats")
            except Exception as e:
                logger.error(
                    "Error al obtener estadísticas de la base de datos: %s",
                    str(e)
                )
                status["error"] = f"Error al obtener estadísticas: {str(e)}"

        # Obtener estado del servidor
        server_status = client.admin.command("serverStatus")
        status["server_status"] = server_status

        # Obtener operaciones lentas (últimas 10)
        try:
            current_ops = client.admin.command("currentOp")
            if current_ops and "inprog" in current_ops:
                slow_ops = [
                    op
                    for op in current_ops["inprog"]
                    if op.get("secs_running", 0) > 1
                    and (
                        op.get("op") in ["query", "insert", "update", "remove"]
                        or "findAndModify" in str(op.get("command", {}))
                    )
                ]
                status["slow_ops"] = slow_ops[:10]
            else:
                status["slow_ops"] = []
        except Exception as e:
            logger.error("Error al obtener operaciones lentas: %s", str(e))
            status["slow_ops"] = []

    except Exception as e:
        status["error"] = f"Error al obtener estadísticas: {str(e)}"
        logger.error(
            "Error en db_monitor: %s\n%s",
            str(e),
            traceback.format_exc()
        )

    return render_template("admin/db_monitor.html", status=status)

@admin_database_bp.route("/performance", methods=["GET", "POST"])
@admin_required
def db_performance():
    """
    Ejecuta y muestra pruebas de rendimiento.
    """
    results = None

    if request.method == "POST":
        try:
            # Obtener parámetros del formulario
            num_ops = int(request.form.get("num_ops", 100))
            batch_size = int(request.form.get("batch_size", 10))

            # Ejecutar pruebas de rendimiento
            db = get_mongo_db()
            if db is None:
                results = {
                    "status": "error",
                    "message": "No se pudo acceder a la base de datos",
                }
                return render_template("admin/db_performance.html", results=results)

            test_collection = db.performance_test

            # Limpiar colección de prueba
            test_collection.drop()

            # Prueba de inserción
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                batch = [
                    {"value": j, "timestamp": datetime.utcnow()}
                    for j in range(i, min(i + batch_size, num_ops))
                ]
                test_collection.insert_many(batch)
            insert_time = time.time() - start_time

            # Prueba de consulta
            start_time = time.time()
            for _ in range(num_ops):
                list(test_collection.find().limit(10))
            query_time = time.time() - start_time

            # Prueba de actualización
            start_time = time.time()
            for i in range(0, num_ops, batch_size):
                test_collection.update_many(
                    {
                        "_id": {
                            "$in": [
                                doc["_id"]
                                for doc in test_collection.find()
                                .skip(i)
                                .limit(batch_size)
                            ]
                        }
                    },
                    {"$set": {"updated": True}},
                )
            update_time = time.time() - start_time

            # Limpiar
            test_collection.drop()

            # Crear métricas con los resultados
            insert_metrics = {
                "time": insert_time,
                "ops_sec": num_ops / insert_time if insert_time > 0 else 0,
            }
            query_metrics = {
                "time": query_time,
                "ops_sec": num_ops / query_time if query_time > 0 else 0,
            }
            update_metrics = {
                "time": update_time,
                "ops_sec": num_ops / update_time if update_time > 0 else 0,
            }

            # Estructurar los resultados según lo esperado por la plantilla
            results = {
                "status": "success",
                "operations": num_ops,
                "batch_size": batch_size,
                "metrics": {
                    "insert": insert_metrics,
                    "query": query_metrics,
                    "update": update_metrics,
                },
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            results = {
                "status": "error",
                "message": f"Error al ejecutar pruebas: {str(e)}",
                "traceback": traceback.format_exc(),
            }
            logger.error(
                "Error en db_performance: %s\n%s",
                str(e),
                results['traceback']
            )

    return render_template("admin/db_performance.html", results=results)

@admin_database_bp.route("/scripts", methods=["GET", "POST"])
@admin_required
def db_scripts():
    """
    Maneja la ejecución de scripts de base de datos desde la interfaz de administración.
    """
    import glob
    import shlex

    # Configuración de directorios
    scripts_dir = os.path.join(os.getcwd(), "tools", "db_utils")

    # Lista de scripts permitidos (solo .py y que no empiecen con _)
    blacklist = {"__init__.py", "google_drive_utils.py"}
    scripts = []

    # Obtener información detallada de cada script
    for script_path in glob.glob(os.path.join(scripts_dir, "*.py")):
        script_name = os.path.basename(script_path)
        if script_name.startswith("_") or script_name in blacklist:
            continue

        # Obtener descripción del script (primera línea de comentario)
        description = "Sin descripción"
        try:
            with open(script_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") and "descripci" in line.lower():
                        description = line.lstrip("#").strip()
                        break
        except Exception as e:
            description = f"Error al leer descripción: {str(e)}"

        scripts.append(
            {
                "name": script_name,
                "path": script_path,
                "description": description,
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(script_path)
                ).strftime("%Y-%m-%d %H:%M"),
            }
        )

    # Ordenar scripts por nombre
    scripts = sorted(scripts, key=lambda x: x["name"])

    # Variables para el formulario
    result = None
    error = None
    selected_script = None
    args = ""
    duration = None

    # Procesar envío del formulario
    if request.method == "POST":
        selected_script = request.form.get("script")
        args = request.form.get("args", "").strip()

        # Validar script seleccionado
        if not selected_script or not selected_script.endswith(".py"):
            error = "Script no válido."
        else:
            # Verificar que el script esté en la lista permitida
            script_info = next(
                (s for s in scripts if s["name"] == selected_script), None
            )
            if not script_info:
                error = "Script no permitido."
            else:
                # Construir comando de forma segura
                cmd = [sys.executable, script_info["path"]]

                # Validar y añadir argumentos
                if args:
                    try:
                        # Validar argumentos (solo permitir ciertos caracteres)
                        if not all(c.isalnum() or c in " -_=." for c in args):
                            raise ValueError(
                                "Caracteres no permitidos en los argumentos"
                            )

                        # Añadir argumentos de forma segura
                        cmd.extend(shlex.split(args))
                    except Exception as e:
                        error = f"Error en los argumentos: {str(e)}"

                # Ejecutar el script
                if not error:
                    start_time = time.time()
                    try:
                        # Ejecutar con timeout de 5 minutos
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=scripts_dir,  # Ejecutar desde el directorio del script
                        )

                        try:
                            out, err = proc.communicate(
                                timeout=300
                            )  # 5 minutos de timeout
                            duration = round(time.time() - start_time, 2)
                            result = out
                            error = err if err and err.strip() else None

                            # Registrar en log de auditoría
                            audit_log(
                                "db_script_execution",
                                user_id=session.get('user_id'),
                                details={
                                    "script": selected_script,
                                    "args": args,
                                    "duration_seconds": duration,
                                    "username": session.get('username', 'desconocido')
                                }
                            )

                            # Añadir mensaje de éxito
                            flash(
                                f"Script ejecutado correctamente en {duration} segundos.",
                                "success",
                            )

                        except subprocess.TimeoutExpired:
                            proc.kill()
                            error = "El script excedió el tiempo máximo de ejecución (5 minutos)"

                    except Exception as e:
                        error = f"Error al ejecutar el script: {str(e)}"

    # Mensaje de advertencia de seguridad
    warning = (
        "⚠️ ADVERTENCIA: La ejecución de scripts puede afectar la base de datos. "
        "Asegúrate de entender lo que hace el script antes de ejecutarlo. "
        "Se recomienda probar en un entorno de desarrollo primero."
    )

    return render_template(
        "admin/db_scripts.html",
        scripts=scripts,
        result=result,
        error=error,
        selected_script=selected_script,
        args=args,
        duration=duration,
        warning=warning,
    )
