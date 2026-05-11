# Script: admin_logs.py
# Descripción: Rutas administrativas para consulta, descarga y limpieza de logs.
# Autor: EDF Developer

import os
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, send_file

from app.decorators import admin_required as admin_required_logs


# Definir el blueprint con el prefijo de URL correcto
# Cambiamos el nombre a 'admin' para que coincida con el prefijo
admin_logs_bp = Blueprint("admin_logs", __name__)

# Decorador para restringir acceso solo a admin (importamos el decorador principal)

LOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../logs/flask_debug.log")
)


@admin_logs_bp.route("/logs")
@admin_required_logs
def logs_manual():
    return render_template("admin/logs_manual.html")


@admin_logs_bp.route("/logs/tail")
@admin_required_logs
def logs_tail():
    import os
    from datetime import datetime

    # Obtener parámetros
    n = int(request.args.get("n", 20))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    keyword = request.args.get("keyword", "").strip()
    log_file = request.args.get("log_file", "flask_debug.log")

    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)

    if not os.path.isfile(log_path):
        return (
            jsonify(
                {
                    "logs": [f"Archivo no encontrado: {log_file}\n"],
                    "error": "Archivo no encontrado",
                }
            ),
            404,
        )

    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Aplicar filtros combinados
        filtered_lines = []
        date_format = "%Y-%m-%d"

        # Preparar filtros de fecha
        date_from_obj = None
        date_to_obj = None
        if date_from:
            date_from_obj = datetime.strptime(date_from, date_format).date()
        if date_to:
            date_to_obj = datetime.strptime(date_to, date_format).date()

        for line in lines:
            # Aplicar filtro de palabra clave
            if keyword and keyword.lower() not in line.lower():
                continue

            # Aplicar filtros de fecha
            if date_from_obj or date_to_obj:
                # Extraer la fecha del log (asumiendo formato de fecha al inicio de la
                # línea)
                log_date_str = " ".join(
                    line.split()[:2]
                )  # Toma los dos primeros segmentos (fecha y hora)
                try:
                    log_datetime = datetime.strptime(
                        log_date_str, "%Y-%m-%d %H:%M:%S,%f"
                    )
                    log_date = log_datetime.date()

                    # Aplicar filtros de fecha
                    if date_from_obj and log_date < date_from_obj:
                        continue
                    if date_to_obj and log_date > date_to_obj:
                        continue

                    filtered_lines.append(line)
                except ValueError:
                    # Si no se puede extraer la fecha, incluir la línea por defecto
                    filtered_lines.append(line)
            else:
                # Si no hay filtro de fechas, solo aplicar filtro de palabra clave
                filtered_lines.append(line)

        # Aplicar límite de líneas si se especificó
        result_lines = filtered_lines[-n:] if n > 0 else filtered_lines

        return jsonify(
            {
                "logs": result_lines,
                "total_lines": len(lines),
                "filtered_lines": len(result_lines),
            }
        )

    except (OSError, PermissionError, UnicodeError) as e:
        return (
            jsonify(
                {
                    "logs": [f"Error al leer el archivo de log: {str(e)}\n"],
                    "error": str(e),
                }
            ),
            500,
        )


@admin_logs_bp.route("/logs/search")
@admin_required_logs
def logs_search():
    import os

    kw = request.args.get("kw", "").strip()
    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        from flask import abort

        abort(404, description=f"Archivo no encontrado: {log_file}")
    if not kw:
        return jsonify({"logs": []})  # Esto es éxito, no error, se mantiene igual.
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        lines = [line for line in f if kw.lower() in line.lower()]
    return jsonify({"logs": lines})


@admin_logs_bp.route("/logs/download")
@admin_required_logs
def logs_download():
    import os

    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return "Archivo no encontrado", 404
    return send_file(log_path, as_attachment=True, download_name=log_file)


@admin_logs_bp.route("/logs/clear", methods=["POST"])
@admin_required_logs
def logs_clear():
    import os
    from datetime import datetime

    log_file = request.args.get("log_file", "flask_debug.log")
    lines = request.form.get("lines")
    date = request.form.get("date")

    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)

    if not os.path.isfile(log_path):
        return jsonify({"status": f"Archivo no encontrado: {log_file}"}), 404

    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        if not all_lines:
            return jsonify({"status": f"Log {log_file} ya está vacío"}), 200

        lines_to_keep = []

        if lines:
            # Truncar por número de líneas
            try:
                num_lines = int(lines)
                if num_lines > 0:
                    lines_to_keep = all_lines[-num_lines:]
                else:
                    lines_to_keep = []
            except ValueError:
                return jsonify({"status": "Número de líneas inválido"}), 400

        elif date:
            # Truncar por fecha
            try:
                cutoff_date = datetime.strptime(date, "%Y-%m-%d").date()
                lines_to_keep = []

                for line in all_lines:
                    # Extraer la fecha del log (asumiendo formato de fecha al inicio de
                    # la línea)
                    log_date_str = " ".join(line.split()[:2])
                    try:
                        log_datetime = datetime.strptime(
                            log_date_str, "%Y-%m-%d %H:%M:%S,%f"
                        )
                        log_date = log_datetime.date()

                        # Mantener líneas desde la fecha de corte en adelante
                        if log_date >= cutoff_date:
                            lines_to_keep.append(line)
                    except ValueError:
                        # Si no se puede extraer la fecha, mantener la línea por defecto
                        lines_to_keep.append(line)

            except ValueError:
                return (
                    jsonify({"status": "Formato de fecha inválido. Use YYYY-MM-DD"}),
                    400,
                )
        else:
            # Si no se especifican parámetros, limpiar todo
            lines_to_keep = []

        # Escribir las líneas que se van a mantener
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(lines_to_keep)

        lines_removed = len(all_lines) - len(lines_to_keep)

        if lines:
            status_msg = f"Log {log_file} truncado: se mantuvieron las últimas {len(lines_to_keep)} líneas"
        elif date:
            status_msg = f"Log {log_file} truncado: se mantuvieron {len(lines_to_keep)} líneas desde {date}"
        else:
            status_msg = f"Log {log_file} limpiado completamente"

        return (
            jsonify(
                {
                    "status": status_msg,
                    "lines_removed": lines_removed,
                    "lines_kept": len(lines_to_keep),
                }
            ),
            200,
        )

    except (OSError, PermissionError, UnicodeError) as e:
        return jsonify({"status": f"Error al procesar el archivo: {str(e)}"}), 500


@admin_logs_bp.route("/logs/size")
@admin_required_logs
def logs_size():
    import os

    log_file = request.args.get("log_file", "flask_debug.log")
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
    log_path = os.path.join(logs_dir, log_file)
    if not os.path.isfile(log_path):
        return jsonify({"size": 0, "backups": 0, "error": "Archivo no encontrado"}), 404
    size = os.path.getsize(log_path)
    backups = len([f for f in os.listdir(logs_dir) if f.startswith(log_file + ".")])
    return jsonify({"size": size, "backups": backups})

