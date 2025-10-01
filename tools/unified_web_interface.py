#!/usr/bin/env python3
"""
Interfaz Web Unificada para Gestión de Scripts - EDF CatalogoDeTablas
Combina funcionalidades de spell check y build scripts en una interfaz web
"""

from unified_scripts_manager import UnifiedScriptsManager
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

app = Flask(__name__)
app.secret_key = "unified_scripts_interface_2025"

# Importar el gestor unificado

# Inicializar el gestor
scripts_manager = UnifiedScriptsManager()


@app.route("/")
def index():
    """Página principal con resumen de categorías"""
    categories_summary = {}

    for category, info in scripts_manager.categories.items():
        script_count = len(info["scripts"])
        categories_summary[category] = {
            "name": category.replace("-", " ").title(),
            "description": info["description"],
            "icon": info["icon"],
            "script_count": script_count,
            "scripts": [],
        }

        # Obtener información básica de cada script
        for script_name, script_info in info["scripts"].items():
            script_path = scripts_manager.get_script_path(category, script_name)
            script_summary = {
                "name": script_name,
                "display_name": script_info["name"],
                "description": script_info["description"],
                "type": script_info["type"],
                "exists": script_path.exists(),
                "category": category,
            }
            categories_summary[category]["scripts"].append(script_summary)

    return render_template("unified_interface.html", categories=categories_summary)


@app.route("/category/<category>")
def category_detail(category):
    """Detalle de una categoría específica"""
    if category not in scripts_manager.categories:
        flash(f'Categoría "{category}" no encontrada', "error")
        return redirect(url_for("index"))

    info = scripts_manager.categories[category]
    scripts = []

    for script_name, script_info in info["scripts"].items():
        script_path = scripts_manager.get_script_path(category, script_name)
        script_detail = {
            "name": script_name,
            "display_name": script_info["name"],
            "description": script_info["description"],
            "type": script_info["type"],
            "exists": script_path.exists(),
            "category": category,
            "path": str(script_path),
        }
        scripts.append(script_detail)

    return render_template(
        "category_detail.html",
        category=category,
        category_name=category.replace("-", " ").title(),
        description=info["description"],
        icon=info["icon"],
        scripts=scripts,
    )


@app.route("/spell-check")
def spell_check_dashboard():
    """Dashboard específico para spell check"""
    # Obtener configuración actual
    config = scripts_manager.get_spell_check_config()

    # Calcular estadísticas
    total_words = (
        len(config["pyproject_toml"]["words"])
        + len(config["vscode_settings"]["words"])
        + len(config["cspell_json"]["words"])
    )

    stats = {
        "total_words": total_words,
        "pyproject_words": len(config["pyproject_toml"]["words"]),
        "vscode_words": len(config["vscode_settings"]["words"]),
        "cspell_words": len(config["cspell_json"]["words"]),
        "pyproject_exists": config["pyproject_toml"]["exists"],
        "vscode_exists": config["vscode_settings"]["exists"],
        "cspell_exists": config["cspell_json"]["exists"],
    }

    # Obtener scripts de spell check
    spell_check_scripts = []
    if "spell-check" in scripts_manager.categories:
        for script_name, script_info in scripts_manager.categories["spell-check"][
            "scripts"
        ].items():
            script_path = scripts_manager.get_script_path("spell-check", script_name)
            script_detail = {
                "name": script_name,
                "display_name": script_info["name"],
                "description": script_info["description"],
                "exists": script_path.exists(),
                "path": str(script_path),
            }
            spell_check_scripts.append(script_detail)

    return render_template(
        "spell_check_dashboard.html",
        stats=stats,
        scripts=spell_check_scripts,
        config=config,
    )


@app.route("/execute/<category>/<script>", methods=["POST"])
def execute_script(category, script):
    """Ejecutar un script específico"""
    try:
        # Verificar que el script existe en la categoría
        if category not in scripts_manager.categories:
            return jsonify(
                {"success": False, "error": f'Categoría "{category}" no encontrada'}
            )

        if script not in scripts_manager.categories[category]["scripts"]:
            return jsonify(
                {
                    "success": False,
                    "error": f'Script "{script}" no encontrado en la categoría "{category}"',
                }
            )

        # Ejecutar el script
        result = scripts_manager.execute_script(category, script)

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "message": f'Script "{script}" ejecutado exitosamente',
                    "stdout": result.get("stdout", ""),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": result.get("error", f'Error ejecutando script "{script}"'),
                    "stderr": result.get("stderr", ""),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )


@app.route("/api/scripts")
def api_scripts():
    """API para obtener información de scripts"""
    try:
        result = {}

        for category, info in scripts_manager.categories.items():
            result[category] = {
                "name": category.replace("-", " ").title(),
                "description": info["description"],
                "icon": info["icon"],
                "script_count": len(info["scripts"]),
                "scripts": [],
            }

            for script_name, script_info in info["scripts"].items():
                script_path = scripts_manager.get_script_path(category, script_name)
                script_detail = {
                    "name": script_name,
                    "display_name": script_info["name"],
                    "description": script_info["description"],
                    "type": script_info["type"],
                    "exists": script_path.exists(),
                    "category": category,
                    "path": str(script_path),
                }

                result[category]["scripts"].append(script_detail)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/spell-check/config")
def api_spell_check_config():
    """API para obtener configuración de spell check"""
    try:
        config = scripts_manager.get_spell_check_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health_check():
    """Verificación de salud del sistema"""
    try:
        # Verificar que el gestor funciona
        categories_count = len(scripts_manager.categories)
        total_scripts = sum(
            len(info["scripts"]) for info in scripts_manager.categories.values()
        )

        # Verificar configuración de spell check
        spell_check_config = scripts_manager.get_spell_check_config()
        spell_check_healthy = any(
            [
                spell_check_config["pyproject_toml"]["exists"],
                spell_check_config["vscode_settings"]["exists"],
                spell_check_config["cspell_json"]["exists"],
            ]
        )

        return jsonify(
            {
                "status": "healthy",
                "categories_count": categories_count,
                "total_scripts": total_scripts,
                "spell_check_healthy": spell_check_healthy,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


if __name__ == "__main__":
    print("🚀 Iniciando Interfaz Web Unificada de Scripts...")
    print(f"📁 Directorio base: {scripts_manager.base_dir}")
    print(
        f"🔧 Scripts disponibles: {sum(len(info['scripts']) for info in scripts_manager.categories.values())}"
    )
    print("🌐 Servidor web iniciado en: http://localhost:5003")
    print("📋 Endpoints disponibles:")
    print("   - / : Página principal")
    print("   - /category/<category> : Detalle de categoría")
    print("   - /spell-check : Dashboard de spell check")
    print("   - /execute/<category>/<script> : Ejecutar script")
    print("   - /api/scripts : API de scripts")
    print("   - /api/spell-check/config : API de configuración spell check")
    print("   - /health : Verificación de salud")
    print()

    app.run(host="0.0.0.0", port=5003, debug=True)
