#!/usr/bin/env python3
"""
Interfaz Web para Gestión de Scripts de Build - EDF CatalogoDeTablas
Interfaz gráfica web para ejecutar scripts de build organizados por categorías
"""

import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, url_for

# Agregar el directorio raíz al path para importar el gestor
sys.path.append(str(Path(__file__).parent.parent))
from build_scripts_manager import BuildScriptsManager

app = Flask(__name__)
app.secret_key = "build_scripts_interface_2025"

# Inicializar el gestor de scripts
scripts_manager = BuildScriptsManager()


@app.route("/")
def index():
    """Página principal con categorías"""
    categories = {}

    for category, info in scripts_manager.categories.items():
        categories[category] = {
            "name": category.replace("-", " ").title(),
            "description": info["description"],
            "script_count": len(info["scripts"]),
            "scripts": [],
        }

        # Obtener información de cada script
        for script in info["scripts"]:
            script_path = scripts_manager.build_dir / category / script
            script_info = {
                "name": script,
                "display_name": script.replace(".sh", "").replace("_", " ").title(),
                "exists": script_path.exists(),
                "category": category,
            }

            if script_path.exists():
                try:
                    original_path = script_path.resolve()
                    script_info["original_path"] = str(original_path)
                    script_info["original_exists"] = original_path.exists()
                    script_info["status"] = "✅" if original_path.exists() else "❌"
                except Exception:
                    script_info["status"] = "❌"
                    script_info["error"] = "Error resolving symlink"
            else:
                script_info["status"] = "❌"
                script_info["error"] = "Symlink not found"

            categories[category]["scripts"].append(script_info)

    return render_template("build_interface.html", categories=categories)


@app.route("/category/<category>")
def category_detail(category):
    """Detalle de una categoría específica"""
    if category not in scripts_manager.categories:
        flash(f'Categoría "{category}" no encontrada', "error")
        return redirect(url_for("index"))

    info = scripts_manager.categories[category]
    scripts = []

    for script in info["scripts"]:
        script_path = scripts_manager.build_dir / category / script
        script_info = {
            "name": script,
            "display_name": script.replace(".sh", "").replace("_", " ").title(),
            "exists": script_path.exists(),
            "category": category,
        }

        if script_path.exists():
            try:
                original_path = script_path.resolve()
                script_info["original_path"] = str(original_path)
                script_info["original_exists"] = original_path.exists()
                script_info["status"] = "✅" if original_path.exists() else "❌"
            except Exception as e:
                script_info["status"] = "❌"
                script_info["error"] = f"Error: {str(e)}"
        else:
            script_info["status"] = "❌"
            script_info["error"] = "Symlink not found"

        scripts.append(script_info)

    return render_template(
        "category_detail.html",
        category=category,
        category_name=category.replace("-", " ").title(),
        description=info["description"],
        scripts=scripts,
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
        success = scripts_manager.execute_script(category, script)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f'Script "{script}" ejecutado exitosamente',
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": f'Error ejecutando script "{script}"',
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
                "script_count": len(info["scripts"]),
                "scripts": [],
            }

            for script in info["scripts"]:
                script_path = scripts_manager.build_dir / category / script
                script_info = {
                    "name": script,
                    "display_name": script.replace(".sh", "").replace("_", " ").title(),
                    "exists": script_path.exists(),
                    "category": category,
                }

                if script_path.exists():
                    try:
                        original_path = script_path.resolve()
                        script_info["original_path"] = str(original_path)
                        script_info["original_exists"] = original_path.exists()
                        script_info["status"] = "✅" if original_path.exists() else "❌"
                    except Exception:
                        script_info["status"] = "❌"
                        script_info["error"] = "Error resolving symlink"
                else:
                    script_info["status"] = "❌"
                    script_info["error"] = "Symlink not found"

                result[category]["scripts"].append(script_info)

        return jsonify(result)

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

        # Verificar directorio de build
        build_dir_exists = scripts_manager.build_dir.exists()

        return jsonify(
            {
                "status": "healthy",
                "categories_count": categories_count,
                "total_scripts": total_scripts,
                "build_dir_exists": build_dir_exists,
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
    print("🚀 Iniciando Interfaz Web de Scripts de Build...")
    print(f"📁 Directorio base: {scripts_manager.base_dir}")
    print(
        f"🔧 Scripts disponibles: {sum(len(info['scripts']) for info in scripts_manager.categories.values())}"
    )
    print("🌐 Servidor web iniciado en: http://localhost:5002")
    print("📋 Endpoints disponibles:")
    print("   - / : Página principal")
    print("   - /category/<category> : Detalle de categoría")
    print("   - /execute/<category>/<script> : Ejecutar script")
    print("   - /api/scripts : API de scripts")
    print("   - /health : Verificación de salud")
    print()

    app.run(host="0.0.0.0", port=5002, debug=True)
