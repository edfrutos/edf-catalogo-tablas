#!/usr/bin/env python3
# Script intermediario para ejecutar scripts desde la aplicación web
# Este script se ejecuta con los permisos adecuados y devuelve los resultados

import datetime
import json
import os
import platform
import stat
import subprocess
import sys
import traceback


def run_script(script_path):
    """Ejecuta un script y devuelve su salida en formato JSON"""
    result = {
        "script": os.path.basename(script_path),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "exit_code": None,
        "output": "",
        "error": "",
        "diagnostics": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "user": os.getenv("USER", subprocess.getoutput("whoami")),
            "script_runner_path": os.path.abspath(__file__),
        },
    }

    # Verificar que el script existe
    if not os.path.exists(script_path):
        result["error"] = f"Script no encontrado: {script_path}"
        result["diagnostics"]["script_exists"] = False
        result["diagnostics"]["absolute_path"] = os.path.abspath(script_path)
        result["diagnostics"]["parent_dir_exists"] = os.path.exists(
            os.path.dirname(script_path)
        )
        return result

    # Recopilar información sobre el script
    try:
        st = os.stat(script_path)
        result["diagnostics"]["script_info"] = {
            "size": st.st_size,
            "permissions": stat.filemode(st.st_mode),
            "owner": st.st_uid,
            "group": st.st_gid,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "is_executable": os.access(script_path, os.X_OK),
            "is_readable": os.access(script_path, os.R_OK),
            "absolute_path": os.path.abspath(script_path),
            "extension": os.path.splitext(script_path)[1],
        }
    except Exception as e:
        result["diagnostics"]["script_info_error"] = str(e)

    # Verificar que el script tiene permisos de ejecución
    if not os.access(script_path, os.X_OK):
        try:
            # Intentar dar permisos de ejecución
            os.chmod(script_path, 0o755)
            result["diagnostics"]["permissions_changed"] = True
        except Exception as e:
            result["error"] = (
                f"No se pudieron establecer permisos de ejecución: {str(e)}"
            )
            result["diagnostics"]["permissions_error"] = str(e)
            return result

    try:
        # Determinar el comando adecuado según la extensión
        _, ext = os.path.splitext(script_path)
        if ext == ".py":
            cmd = [sys.executable, script_path]
        elif ext == ".sh":
            cmd = ["/bin/bash", script_path]
        else:
            cmd = [script_path]

        result["diagnostics"]["command"] = cmd

        # Ejecutar el script
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(script_path),
        )

        result["exit_code"] = process.returncode
        result["output"] = process.stdout
        result["error"] = process.stderr

    except subprocess.TimeoutExpired:
        result["error"] = (
            "El script tardó demasiado tiempo en ejecutarse (más de 30 segundos)"
        )
        result["diagnostics"]["timeout"] = True
    except Exception as e:
        result["error"] = f"Error al ejecutar el script: {str(e)}"
        result["diagnostics"]["exception"] = str(e)
        result["diagnostics"]["traceback"] = traceback.format_exc()

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Debe especificar la ruta del script a ejecutar"}))
        sys.exit(1)

    script_path = sys.argv[1]
    result = run_script(script_path)

    # Imprimir el resultado en formato JSON
    print(json.dumps(result))
