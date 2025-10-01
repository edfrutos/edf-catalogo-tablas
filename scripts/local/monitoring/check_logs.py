#!/usr/bin/env python3
# Script para analizar logs y detectar problemas de ejecución de scripts
# Creado: 17/05/2025

import argparse
import datetime
import os
import re
import sys
from collections import Counter


def print_header(message):
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)


def analyze_log_file(log_path, max_lines=1000, search_term=None):
    """Analiza un archivo de log para detectar errores relacionados con scripts"""
    if not os.path.exists(log_path):
        return {"success": False, "error": f"El archivo de log no existe: {log_path}"}

    try:
        # Patrones para detectar errores comunes
        error_patterns = {
            "script_not_found": re.compile(
                r"Script no encontrado|No such file or directory|Cannot find|404"
            ),
            "permission_denied": re.compile(r"Permission denied|permiso denegado|403"),
            "timeout": re.compile(r"timeout|tiempo de espera agotado|timed out"),
            "syntax_error": re.compile(r"SyntaxError|syntax error|error de sintaxis"),
            "import_error": re.compile(
                r"ImportError|ModuleNotFoundError|No module named"
            ),
            "execution_error": re.compile(
                r"Error al ejecutar|execution failed|failed to execute"
            ),
        }

        # Contadores para diferentes tipos de errores
        error_counts = Counter()
        error_examples = {}

        # Leer las últimas líneas del archivo de log
        with open(log_path, "r", errors="ignore") as f:
            # Si el archivo es muy grande, leer solo las últimas líneas
            if search_term:
                lines = [line for line in f if search_term.lower() in line.lower()]
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]
            else:
                lines = f.readlines()
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]

        # Analizar cada línea del log
        for line in lines:
            line = line.strip()

            # Verificar cada patrón de error
            for error_type, pattern in error_patterns.items():
                if pattern.search(line):
                    error_counts[error_type] += 1

                    # Guardar ejemplos de cada tipo de error
                    if (
                        error_type not in error_examples
                        or len(error_examples[error_type]) < 3
                    ):
                        if error_type not in error_examples:
                            error_examples[error_type] = []
                        error_examples[error_type].append(line)

        # Preparar el resultado
        result = {
            "success": True,
            "log_file": log_path,
            "lines_analyzed": len(lines),
            "error_counts": dict(error_counts),
            "error_examples": error_examples,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Error al analizar el archivo de log: {str(e)}",
        }


def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Analiza logs para detectar problemas de ejecución de scripts"
    )
    parser.add_argument("--log", help="Ruta al archivo de log a analizar", default=None)
    parser.add_argument(
        "--lines", type=int, help="Número máximo de líneas a analizar", default=1000
    )
    parser.add_argument(
        "--search", help="Término de búsqueda para filtrar líneas", default=None
    )
    args = parser.parse_args()

    # Definir el directorio raíz
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, "logs")

    print_header("ANÁLISIS DE LOGS PARA DETECTAR PROBLEMAS DE SCRIPTS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio de logs: {logs_dir}")

    # Determinar qué logs analizar
    log_files = []
    if args.log:
        log_files.append(args.log)
    else:
        # Analizar los logs principales
        gunicorn_error_log = os.path.join(logs_dir, "gunicorn_error.log")
        flask_debug_log = os.path.join(logs_dir, "flask_debug.log")

        if os.path.exists(gunicorn_error_log):
            log_files.append(gunicorn_error_log)

        if os.path.exists(flask_debug_log):
            log_files.append(flask_debug_log)

    # Analizar cada archivo de log
    for log_file in log_files:
        print_header(f"ANALIZANDO: {os.path.basename(log_file)}")

        result = analyze_log_file(log_file, args.lines, args.search)

        if result["success"]:
            print(f"Archivo: {result['log_file']}")
            print(f"Líneas analizadas: {result['lines_analyzed']}")
            print("\nResumen de errores encontrados:")

            if not result["error_counts"]:
                print("  No se encontraron errores relacionados con scripts.")
            else:
                for error_type, count in result["error_counts"].items():
                    print(f"  {error_type}: {count} ocurrencias")

                print("\nEjemplos de errores encontrados:")
                for error_type, examples in result["error_examples"].items():
                    print(f"\n  {error_type}:")
                    for i, example in enumerate(examples, 1):
                        print(
                            f"    {i}. {example[:150]}..."
                            if len(example) > 150
                            else f"    {i}. {example}"
                        )
        else:
            print(f"Error: {result['error']}")

    print_header("RECOMENDACIONES")
    print(
        "1. Si encuentra errores 'script_not_found', verifique las rutas de los scripts"
    )
    print(
        "2. Para errores de 'permission_denied', ejecute el script fix_script_permissions.sh"
    )
    print("3. Para errores de 'import_error', verifique las dependencias del script")
    print(
        "4. Si hay errores de 'timeout', considere aumentar el tiempo de espera en script_runner.py"
    )
    print("5. Después de realizar cambios, reinicie el servidor con restart_server.sh")


if __name__ == "__main__":
    main()
