# Script: admin_db_routes.py
# Descripción: Rutas administrativas de base de datos, monitorización y rendimiento.
# Autor: EDF Developer

import os
import time
import traceback
from datetime import datetime
from typing import Any

from flask import current_app, flash, jsonify, render_template, request, session

from app.audit import audit_log
from app.database import get_mongo_client, get_mongo_db
from app.decorators import admin_required


def register_admin_db_routes(admin_bp) -> None:
    """Registra rutas administrativas de base de datos sobre el blueprint admin."""

    @admin_bp.route("/db-scripts", methods=["GET", "POST"])
    @admin_required
    def db_scripts():
        """
        Maneja la ejecución de scripts de base de datos desde la interfaz de administración.

        Permite ejecutar scripts de mantenimiento de la base de datos con argumentos opcionales.
        Incluye medidas de seguridad para prevenir ejecución de comandos maliciosos.
        """
        import glob
        import shlex
        import subprocess
        import time
        from datetime import datetime

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
            except (OSError, PermissionError, UnicodeError) as e:
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
                    cmd = ["python3", script_info["path"]]

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
                        except (ValueError, TypeError) as e:
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
                                    user_id=session.get("user_id"),
                                    details={
                                        "script": selected_script,
                                        "args": args,
                                        "duration_seconds": duration,
                                        "username": session.get("username", "desconocido"),
                                    },
                                )

                                # Añadir mensaje de éxito
                                flash(
                                    f"Script ejecutado correctamente en {duration} segundos.",
                                    "success",
                                )

                            except subprocess.TimeoutExpired:
                                proc.kill()
                                error = "El script excedió el tiempo máximo de ejecución (5 minutos)"

                        except (OSError, PermissionError, TimeoutError) as e:
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


    @admin_bp.route("/db-status")
    @admin_required
    def db_status():
        """Muestra el estado de la conexión a MongoDB"""
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
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    current_app.logger.error(f"Error al obtener colecciones: {str(e)}")
                    status["collections"] = []
                    status["error"] = f"Error al obtener colecciones: {str(e)}"

            # Obtener información del servidor y convertir objetos no serializables
            def convert_timestamps(obj: Any) -> Any:
                from datetime import datetime

                from bson import Timestamp
                from bson.objectid import ObjectId

                if isinstance(obj, (list, tuple)):
                    return [convert_timestamps(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: convert_timestamps(v) for k, v in obj.items()}
                elif isinstance(obj, Timestamp):
                    return {
                        "timestamp": obj.time,
                        "increment": obj.inc,
                        "as_datetime": datetime.fromtimestamp(obj.time).isoformat(),
                        "_type": "Timestamp",
                    }
                elif isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, bytes):
                    # Convertir bytes a string si es posible, o a una representación en
                    # base64
                    try:
                        return obj.decode("utf-8")
                    except UnicodeDecodeError:
                        import base64

                        return {
                            "_type": "bytes",
                            "base64": base64.b64encode(obj).decode("ascii"),
                            "length": len(obj),
                        }
                elif hasattr(obj, "isoformat"):  # Para objetos datetime
                    return obj.isoformat()
                elif hasattr(obj, "items"):  # Para objetos tipo dict
                    return {str(k): convert_timestamps(v) for k, v in obj.items()}
                elif hasattr(obj, "__dict__"):  # Para objetos con __dict__
                    return convert_timestamps(obj.__dict__)
                elif isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                else:
                    # Para cualquier otro tipo, devolver su representación como string
                    return str(obj)

            # Obtener y procesar la información del servidor
            server_info = client.server_info()
            status["server_info"] = convert_timestamps(server_info)

            # Obtener y procesar estadísticas del servidor
            try:
                server_status = client.admin.command("serverStatus")
                status["server_status"] = convert_timestamps(server_status)
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                status["server_status"] = {
                    "error": f"No se pudo obtener el estado del servidor: {str(e)}"
                }

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            status["error"] = f"Error al conectar con MongoDB: {str(e)}"
            current_app.logger.error(
                f"Error en db_status: {str(e)}\n{traceback.format_exc()}"
            )
        return render_template("admin/db_status.html", status=status)


    @admin_bp.route("/db/monitor")
    @admin_required
    def db_monitor():
        """Página de monitoreo en tiempo real de la base de datos"""
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
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    current_app.logger.error(
                        f"Error al obtener estadísticas de la base de datos: {str(e)}"
                    )
                    status["error"] = f"Error al obtener estadísticas: {str(e)}"

            # Obtener estado del servidor
            server_status = client.admin.command("serverStatus")
            status["server_status"] = server_status

            # Inicializar contadores de operaciones si no existen
            if "opcounters" not in session:
                session["opcounters"] = {
                    "query": 0,
                    "insert": 0,
                    "update": 0,
                    "delete": 0,
                    "getmore": 0,
                    "command": 0,
                }

            # Guardar timestamp de la última actualización
            session["last_update"] = time.time()

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
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                current_app.logger.error(f"Error al obtener operaciones lentas: {str(e)}")
                status["slow_ops"] = []

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            status["error"] = f"Error al obtener estadísticas: {str(e)}"
            current_app.logger.error(
                f"Error en db_monitor: {str(e)}\n{traceback.format_exc()}"
            )

        return render_template("admin/db_monitor.html", status=status)


    # Variables globales para el seguimiento de operaciones
    last_ops: dict[str, int] = {}  # type: ignore
    last_update = time.time()


    @admin_bp.route("/api/db/ops")
    @admin_required
    def get_db_ops():
        """
        Endpoint para obtener estadísticas de operaciones en tiempo real.
        Usa variables globales para el seguimiento entre solicitudes.
        """
        global last_ops, last_update

        try:
            client = get_mongo_client()
            if client is None:
                return (
                    jsonify({"success": False, "error": "Cliente MongoDB no disponible"}),
                    500,
                )
            server_status = client.admin.command("serverStatus")

            # Obtener contadores actuales
            current_ops = server_status.get("opcounters", {})
            current_time = time.time()

            # Calcular operaciones por segundo
            time_diff = current_time - last_update
            ops_per_sec = {}

            if last_ops and time_diff > 0:
                for op_type in [
                    "query",
                    "insert",
                    "update",
                    "delete",
                    "getmore",
                    "command",
                ]:
                    if op_type in current_ops and op_type in last_ops:
                        ops_diff = current_ops[op_type] - last_ops[op_type]
                        ops_per_sec[op_type] = round(ops_diff / time_diff, 2)

            # Actualizar estado para la próxima solicitud
            last_ops = current_ops
            last_update = current_time

            # Obtener información de memoria
            memory = server_status.get("mem", {})

            # Obtener información de conexiones
            connections = server_status.get("connections", {})

            # Obtener operaciones lentas
            current_op = client.admin.current_op()
            slow_ops = []
            if "inprog" in current_op:
                for op in current_op["inprog"]:
                    if (
                        "secs_running" in op and op["secs_running"] > 1
                    ):  # Operaciones que llevan más de 1 segundo
                        slow_ops.append(
                            {
                                "opid": op.get("opid"),
                                "secs_running": op.get("secs_running"),
                                "op": op.get("op"),
                                "ns": op.get("ns"),
                                "client": op.get("client"),
                            }
                        )

            return jsonify(
                {
                    "success": True,
                    "ops_per_sec": ops_per_sec,
                    "memory": memory,
                    "connections": connections,
                    "slow_ops": (
                        slow_ops[:10] if slow_ops else []
                    ),  # Devolver solo las 10 operaciones más lentas
                    "timestamp": current_time,
                }
            )

        except (
            ConnectionError,
            TimeoutError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            current_app.logger.error(f"Error en get_db_ops: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return (
                jsonify(
                    {"success": False, "error": str(e), "traceback": traceback.format_exc()}
                ),
                500,
            )


    @admin_bp.route("/db/performance", methods=["GET", "POST"])
    @admin_required
    def db_performance():
        """Ejecuta y muestra pruebas de rendimiento"""
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

            except (
                ConnectionError,
                TimeoutError,
                AttributeError,
                KeyError,
                TypeError,
                ValueError,
            ) as e:
                results = {
                    "status": "error",
                    "message": f"Error al ejecutar pruebas: {str(e)}",
                    "traceback": traceback.format_exc(),
                }
                current_app.logger.error(
                    f"Error en db_performance: {str(e)}\n{results['traceback']}"
                )

        return render_template("admin/db_performance.html", results=results)
