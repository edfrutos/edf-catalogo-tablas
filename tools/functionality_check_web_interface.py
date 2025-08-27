#!/usr/bin/env python3
"""
Interfaz Web para Verificación de Funcionalidad - EDF_CatalogoDeTablas
Interfaz web para ejecutar y visualizar los resultados de verificación

Autor: Sistema de verificación automática
Fecha: 2025-08-27
Python: 3.10+
"""

import os  # pyright: ignore[reportUnusedImport]
import sys
import json
import threading
import time  # pyright: ignore[reportUnusedImport]
from datetime import datetime
from pathlib import Path
from flask import (
    Flask,
    render_template,
    jsonify,
    request,  # pyright: ignore[reportUnusedImport]
    flash,
    redirect,
    url_for,
)
import logging

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

# Importar el verificador después de configurar el path
from app_functionality_checker import AppFunctionalityChecker  # noqa: E402

app = Flask(__name__)
app.secret_key = "functionality_check_interface_2025"

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variable global para almacenar resultados
current_results = None
check_in_progress = False


@app.route("/")
def index():
    """Página principal de la interfaz"""
    return render_template("functionality_check_index.html")


@app.route("/favicon.ico")
def favicon():
    """Favicon para evitar errores 404"""
    return "", 204  # No content


@app.route("/run-check", methods=["GET", "POST"])
def run_check():
    """Ejecutar verificación de funcionalidad"""
    if request.method == "GET":
        # Si es GET, redirigir al inicio
        flash("ℹ️ Usa el botón para ejecutar la verificación", "info")
        return redirect(url_for("index"))

    # Método POST
    global current_results, check_in_progress

    if check_in_progress:
        flash("⚠️ Ya hay una verificación en progreso", "warning")
        return redirect(url_for("index"))

    check_in_progress = True

    def run_check_thread():
        global current_results, check_in_progress
        try:
            checker = AppFunctionalityChecker()
            current_results = checker.run_all_checks()
            logger.info("✅ Verificación completada exitosamente")
        except Exception as e:
            logger.error(f"❌ Error durante la verificación: {e}")
            current_results = {"error": str(e)}
        finally:
            check_in_progress = False

    # Ejecutar verificación en hilo separado
    thread = threading.Thread(target=run_check_thread)
    thread.start()

    flash("🚀 Verificación iniciada. Redirigiendo a resultados...", "info")
    return redirect(url_for("results"))


@app.route("/results")
def results():
    """Mostrar resultados de la verificación"""
    global current_results, check_in_progress

    if check_in_progress:
        return render_template("check_in_progress.html")

    if current_results is None:
        flash(
            "⚠️ No hay resultados disponibles. Ejecuta una verificación primero.",
            "warning",
        )
        return redirect(url_for("index"))

    if "error" in current_results:
        return render_template("check_error.html", error=current_results["error"])

    return render_template(
        "functionality_results.html", results=current_results["results"]
    )


@app.route("/api/status")
def api_status():
    """API para verificar estado de la verificación"""
    global check_in_progress, current_results

    return jsonify(
        {
            "check_in_progress": check_in_progress,
            "has_results": current_results is not None,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/results")
def api_results():
    """API para obtener resultados en formato JSON"""
    global current_results

    if current_results is None:
        return jsonify({"error": "No hay resultados disponibles"}), 404

    return jsonify(current_results["results"])


@app.route("/history")
def history():
    """Mostrar historial de verificaciones"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return render_template("no_history.html")

    # Buscar archivos de verificación
    check_files = list(logs_dir.glob("functionality_check_*.json"))
    check_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    history_data = []
    for file_path in check_files[:10]:  # Últimos 10 archivos
        try:
            with open(file_path, "r", encoding="utf-8") as f:  # noqa: UP015
                data = json.load(f)

            history_data.append(
                {
                    "filename": file_path.name,
                    "timestamp": data.get("timestamp", ""),
                    "summary": data.get("summary", {}),
                    "file_path": str(file_path),
                }
            )
        except Exception as e:
            logger.error(f"Error leyendo {file_path}: {e}")

    return render_template("check_history.html", history=history_data)


@app.route("/view-result/<filename>")
def view_result(filename):
    """Ver resultado específico del historial"""
    file_path = Path("logs") / filename

    if not file_path.exists():
        flash("❌ Archivo no encontrado", "error")
        return redirect(url_for("history"))

    try:
        with open(file_path, "r", encoding="utf-8") as f:  # noqa: UP015
            data = json.load(f)

        return render_template("functionality_results.html", results=data)
    except Exception as e:
        flash(f"❌ Error leyendo archivo: {e}", "error")
        return redirect(url_for("history"))


def create_templates():
    """Crear templates HTML para la interfaz"""
    templates_dir = Path(__file__).parent / "templates"

    # Template principal
    index_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación de Funcionalidad - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 40px;
        }
        .check-button {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(39, 174, 96, 0.3);
        }
        .check-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        .check-button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #ecf0f1;
            color: #2c3e50;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #3498db;
            color: white;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .flash-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .flash-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .flash-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Verificación de Funcionalidad</h1>
            <p>EDF_CatalogoDeTablas - Sistema de Verificación Automática</p>
        </div>
        
        <div class="content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="flash-message flash-{{ category }}">
                                {{ message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">7</div>
                    <div class="stat-label">Verificaciones</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">160</div>
                    <div class="stat-label">Rutas Registradas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">145</div>
                    <div class="stat-label">Paquetes Optimizados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">351MB</div>
                    <div class="stat-label">Tamaño Entorno</div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <form method="POST" action="{{ url_for('run_check') }}">
                    <button type="submit" class="check-button" id="runCheckBtn">
                        🚀 Ejecutar Verificación Completa
                    </button>
                </form>
            </div>
            
            <div class="nav-links">
                <a href="{{ url_for('results') }}">📊 Ver Últimos Resultados</a>
                <a href="{{ url_for('history') }}">📚 Historial de Verificaciones</a>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh para verificar estado
        setInterval(function() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.check_in_progress) {
                        window.location.href = '/results';
                    }
                });
        }, 2000);
    </script>
</body>
</html>"""

    # Template de resultados
    results_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados de Verificación - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 40px;
        }
        .summary-card {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }
        .summary-status {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .summary-stat {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
        }
        .summary-number {
            font-size: 1.5em;
            font-weight: bold;
        }
        .checks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .check-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }
        .check-card.success {
            border-left-color: #27ae60;
            background: #d5f4e6;
        }
        .check-card.error {
            border-left-color: #e74c3c;
            background: #fadbd8;
        }
        .check-card.warning {
            border-left-color: #f39c12;
            background: #fdeaa7;
        }
        .check-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .check-status {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .check-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .check-details {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .recommendations {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .recommendation {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .recommendation.critical {
            background: #fadbd8;
            color: #721c24;
        }
        .recommendation.optimization {
            background: #fdeaa7;
            color: #856404;
        }
        .recommendation.success {
            background: #d5f4e6;
            color: #155724;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.2em;
            color: #7f8c8d;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Resultados de Verificación</h1>
        </div>
        <div class="content">
            {% if results %}
                <div class="summary-card">
                    <div class="summary-status">{{ results.summary.overall_status }}</div>
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.passed_checks }}/{{ results.summary.total_checks }}</div>
                            <div>Verificaciones Exitosas</div>
                        </div>
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.success_rate }}%</div>
                            <div>Tasa de Éxito</div>
                        </div>
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.critical_checks }}</div>
                            <div>Verificaciones Críticas</div>
                        </div>
                    </div>
                </div>
                <div class="checks-grid">
                    {% for check_name, check_data in results.checks.items() %}
                        <div class="check-card {% if check_data.status == '✅' %}success{% elif check_data.status == '❌' %}error{% else %}warning{% endif %}">
                            <div class="check-header">
                                <div class="check-status">{{ check_data.status }}</div>
                                <div class="check-title">{{ check_name.replace('_', ' ').title() }}</div>
                            </div>
                            <div class="check-details">
                                {% if check_name == 'python_version' %}
                                    Versión actual: {{ check_data.current }}<br>
                                    Requerida: {{ check_data.required }}
                                {% elif check_name == 'dependencies' %}
                                    {% for dep_name, dep_data in check_data.items() %}
                                        {% if dep_name != 'working' and dep_name != 'total' %}
                                            {{ dep_data.status }} {{ dep_data.name }}<br>
                                        {% endif %}
                                    {% endfor %}
                                {% elif check_name == 'flask_app' %}
                                    Tiempo de creación: {{ check_data.creation_time }}s<br>
                                    Total rutas: {{ check_data.total_routes }}<br>
                                    API: {{ check_data.api_routes }} | Admin: {{ check_data.admin_routes }} | Usuario: {{ check_data.user_routes }}
                                {% elif check_name == 'mongodb' %}
                                    Colecciones: {{ check_data.collections_count }}<br>
                                    {% if check_data.collections %}
                                        Primeras: {{ check_data.collections[:3]|join(', ') }}
                                    {% endif %}
                                {% elif check_name == 'package_count' %}
                                    Paquetes instalados: {{ check_data.package_count }}<br>
                                    {% if check_data.optimized %}
                                        ✅ Optimizado
                                    {% else %}
                                        ⚠️ Puede optimizarse
                                    {% endif %}
                                {% elif check_name == 'environment_size' %}
                                    Tamaño: {{ check_data.size }}<br>
                                    {% if check_data.optimized %}
                                        ✅ Optimizado
                                    {% else %}
                                        ⚠️ Puede optimizarse
                                    {% endif %}
                                {% else %}
                                    {% if check_data.working %}
                                        ✅ Funcionando correctamente
                                    {% else %}
                                        ❌ {{ check_data.error or 'Error desconocido' }}
                                    {% endif %}
                                {% endif %}
                            </div>
                        </div>
                    {% endfor %}
                </div>
                
                {% if results.recommendations %}
                    <div class="recommendations">
                        <h3>💡 Recomendaciones</h3>
                        {% for rec in results.recommendations %}
                            <div class="recommendation {{ rec.type }}">
                                {% if rec.type == 'critical' %}🔴{% elif rec.type == 'optimization' %}🟡{% else %}🟢{% endif %}
                                {{ rec.message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% else %}
                <div class="loading">
                    <div class="spinner"></div>
                    <div>Verificación en progreso...</div>
                    <div style="margin-top: 20px; font-size: 0.9em;">
                        Esta página se actualizará automáticamente cuando termine la verificación.
                    </div>
                </div>
            {% endif %}
            
            <div class="nav-links">
                <a href="{{ url_for('index') }}">🏠 Inicio</a>
                <a href="{{ url_for('history') }}">📚 Historial</a>
                <a href="{{ url_for('run_check') }}" onclick="return confirm('¿Ejecutar nueva verificación?')">🔄 Nueva Verificación</a>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh si no hay resultados
        {% if not results %}
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        {% endif %}
    </script>
</body>
</html>"""

    # Guardar templates
    with open(
        templates_dir / "functionality_check_index.html", "w", encoding="utf-8"
    ) as f:
        f.write(index_html)

    with open(templates_dir / "functionality_results.html", "w", encoding="utf-8") as f:
        f.write(results_html)

    # Template de verificación en progreso
    progress_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación en Progreso - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 500px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        p {
            color: #7f8c8d;
            line-height: 1.6;
        }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #ecf0f1;
            border-radius: 5px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            animation: progress 2s ease-in-out infinite;
        }
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h1>🚀 Verificación en Progreso</h1>
        <p>Estamos verificando todas las funcionalidades de la aplicación...</p>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p>Esta página se actualizará automáticamente cuando termine la verificación.</p>
    </div>
    
    <script>
        // Auto-refresh cada 3 segundos
        setInterval(function() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (!data.check_in_progress) {
                        window.location.href = '/results';
                    }
                });
        }, 3000);
    </script>
</body>
</html>"""

    with open(templates_dir / "check_in_progress.html", "w", encoding="utf-8") as f:
        f.write(progress_html)

    # Template de historial
    history_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial de Verificaciones - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 40px;
        }
        .history-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            transition: all 0.3s ease;
        }
        .history-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .history-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .history-date {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .history-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .history-stat {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        .history-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        .history-label {
            color: #7f8c8d;
            font-size: 0.8em;
        }
        .history-actions {
            margin-top: 15px;
            text-align: right;
        }
        .history-actions a {
            display: inline-block;
            padding: 8px 15px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9em;
            transition: all 0.3s ease;
            }
        .history-actions a:hover {
            background: #2980b9;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #ecf0f1;
            color: #2c3e50;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #3498db;
            color: white;
        }
        .no-history {
            text-align: center;
            padding: 50px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Historial de Verificaciones</h1>
        </div>
        
        <div class="content">
            {% if history %}
                {% for item in history %}
                    <div class="history-item">
                        <div class="history-header">
                            <div class="history-title">{{ item.filename }}</div>
                            <div class="history-date">{{ item.timestamp[:19].replace('T', ' ') }}</div>
                        </div>
                        <div class="history-stats">
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.passed_checks }}/{{ item.summary.total_checks }}</div>
                                <div class="history-label">Verificaciones</div>
                            </div>
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.success_rate }}%</div>
                                <div class="history-label">Éxito</div>
                            </div>
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.overall_status }}</div>
                                <div class="history-label">Estado</div>
                            </div>
                        </div>
                        <div class="history-actions">
                            <a href="{{ url_for('view_result', filename=item.filename) }}">📊 Ver Detalles</a>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-history">
                    <h2>📭 No hay historial disponible</h2>
                    <p>Ejecuta tu primera verificación para crear historial.</p>
                </div>
            {% endif %}
            
            <div class="nav-links">
                <a href="{{ url_for('index') }}">🏠 Inicio</a>
                <a href="{{ url_for('run_check') }}">🚀 Nueva Verificación</a>
            </div>
        </div>
    </div>
</body>
</html>"""

    with open(templates_dir / "check_history.html", "w", encoding="utf-8") as f:
        f.write(history_html)

    # Template de error
    error_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error en Verificación - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 600px;
        }
        .error-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 20px;
        }
        .error-message {
            background: #fadbd8;
            color: #721c24;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .nav-links {
            margin-top: 30px;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">❌</div>
        <h1>Error en la Verificación</h1>
        <p>Ocurrió un error durante la verificación de funcionalidad:</p>
        <div class="error-message">{{ error }}</div>
        <div class="nav-links">
            <a href="{{ url_for('index') }}">🏠 Volver al Inicio</a>
            <a href="{{ url_for('run_check') }}">🔄 Intentar de Nuevo</a>
        </div>
    </div>
</body>
</html>"""

    with open(templates_dir / "check_error.html", "w", encoding="utf-8") as f:
        f.write(error_html)

    # Template de no historial
    no_history_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sin Historial - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 500px;
        }
        .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        p {
            color: #7f8c8d;
            line-height: 1.6;
        }
        .nav-links {
            margin-top: 30px;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📭</div>
        <h1>Sin Historial Disponible</h1>
        <p>No se encontraron archivos de verificación anteriores.</p>
        <p>Ejecuta tu primera verificación para crear historial.</p>
        <div class="nav-links">
            <a href="{{ url_for('index') }}">🏠 Volver al Inicio</a>
            <a href="{{ url_for('run_check') }}">🚀 Ejecutar Primera Verificación</a>
        </div>
    </div>
</body>
</html>"""

    with open(templates_dir / "no_history.html", "w", encoding="utf-8") as f:
        f.write(no_history_html)


if __name__ == "__main__":
    # Crear directorio de templates si no existe
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Crear templates HTML
    create_templates()

    print("🌐 Iniciando interfaz web de verificación de funcionalidad...")
    print("📱 Accede a: http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
    """Crear templates HTML para la interfaz"""
    templates_dir = Path(__file__).parent / "templates"

    # Template principal
    index_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación de Funcionalidad - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 40px;
        }
        .check-button {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(39, 174, 96, 0.3);
        }
        .check-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        .check-button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #ecf0f1;
            color: #2c3e50;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #3498db;
            color: white;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .flash-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .flash-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .flash-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Verificación de Funcionalidad</h1>
            <p>EDF_CatalogoDeTablas - Sistema de Verificación Automática</p>
        </div>
        <div class="content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="flash-message flash-{{ category }}">
                                {{ message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">7</div>
                    <div class="stat-label">Verificaciones</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">159</div>
                    <div class="stat-label">Rutas Registradas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">147</div>
                    <div class="stat-label">Paquetes Optimizados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">351MB</div>
                    <div class="stat-label">Tamaño Entorno</div>
                </div>
            </div>
            <div style="text-align: center; margin: 40px 0;">
                <form method="POST" action="{{ url_for('run_check') }}">
                    <button type="submit" class="check-button" id="runCheckBtn">
                        🚀 Ejecutar Verificación Completa
                    </button>
                </form>
            </div>
            <div class="nav-links">
                <a href="{{ url_for('results') }}">📊 Ver Últimos Resultados</a>
                <a href="{{ url_for('history') }}">📚 Historial de Verificaciones</a>
            </div>
        </div>
    </div>
    <script>
        // Auto-refresh para verificar estado
        setInterval(function() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.check_in_progress) {
                        window.location.href = '/results';
                    }
                });
        }, 2000);
    </script>
</body>
</html>"""

    # Template de resultados
    results_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados de Verificación - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 40px;
        }
        .summary-card {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }
        .summary-status {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .summary-stat {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
        }
        .summary-number {
            font-size: 1.5em;
            font-weight: bold;
        }
        .checks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .check-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }
        .check-card.success {
            border-left-color: #27ae60;
            background: #d5f4e6;
        }
        .check-card.error {
            border-left-color: #e74c3c;
            background: #fadbd8;
        }
        .check-card.warning {
            border-left-color: #f39c12;
            background: #fdeaa7;
        }
        .check-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .check-status {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .check-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .check-details {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .recommendations {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .recommendation {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .recommendation.critical {
            background: #fadbd8;
            color: #721c24;
        }
        .recommendation.optimization {
            background: #fdeaa7;
            color: #856404;
        }
        .recommendation.success {
            background: #d5f4e6;
            color: #155724;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.2em;
            color: #7f8c8d;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Resultados de Verificación</h1>
        </div>
        <div class="content">
            {% if results %}
                <div class="summary-card">
                    <div class="summary-status">{{ results.summary.overall_status }}</div>
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.passed_checks }}/{{ results.summary.total_checks }}</div>
                            <div>Verificaciones Exitosas</div>
                        </div>
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.success_rate }}%</div>
                            <div>Tasa de Éxito</div>
                        </div>
                        <div class="summary-stat">
                            <div class="summary-number">{{ results.summary.critical_checks }}</div>
                            <div>Verificaciones Críticas</div>
                        </div>
                    </div>
                </div>
                <div class="checks-grid">
                    {% for check_name, check_data in results.checks.items() %}
                        <div class="check-card {% if check_data.status == '✅' %}success{% elif check_data.status == '❌' %}error{% else %}warning{% endif %}">
                            <div class="check-header">
                                <div class="check-status">{{ check_data.status }}</div>
                                <div class="check-title">{{ check_name.replace('_', ' ').title() }}</div>
                            </div>
                            <div class="check-details">
                                {% if check_name == 'python_version' %}
                                    Versión actual: {{ check_data.current }}<br>
                                    Requerida: {{ check_data.required }}
                                {% elif check_name == 'dependencies' %}
                                    {% for dep_name, dep_data in check_data.items() %}
                                        {% if dep_name != 'working' and dep_name != 'total' %}
                                            {{ dep_data.status }} {{ dep_data.name }}<br>
                                        {% endif %}
                                    {% endfor %}
                                {% elif check_name == 'flask_app' %}
                                    Tiempo de creación: {{ check_data.creation_time }}s<br>
                                    Total rutas: {{ check_data.total_routes }}<br>
                                    API: {{ check_data.api_routes }} | Admin: {{ check_data.admin_routes }} | Usuario: {{ check_data.user_routes }}
                                {% elif check_name == 'mongodb' %}
                                    Colecciones: {{ check_data.collections_count }}<br>
                                    {% if check_data.collections %}
                                        Primeras: {{ check_data.collections[:3]|join(', ') }}
                                    {% endif %}
                                {% elif check_name == 'package_count' %}
                                    Paquetes instalados: {{ check_data.package_count }}<br>
                                    {% if check_data.optimized %}
                                        ✅ Optimizado
                                    {% else %}
                                        ⚠️ Puede optimizarse
                                    {% endif %}
                                {% elif check_name == 'environment_size' %}
                                    Tamaño: {{ check_data.size }}<br>
                                    {% if check_data.optimized %}
                                        ✅ Optimizado
                                    {% else %}
                                        ⚠️ Puede optimizarse
                                    {% endif %}
                                {% else %}
                                    {% if check_data.working %}
                                        ✅ Funcionando correctamente
                                    {% else %}
                                        ❌ {{ check_data.error or 'Error desconocido' }}
                                    {% endif %}
                                {% endif %}
                            </div>
                        </div>
                    {% endfor %}
                </div>
                {% if results.recommendations %}
                    <div class="recommendations">
                        <h3>💡 Recomendaciones</h3>
                        {% for rec in results.recommendations %}
                            <div class="recommendation {{ rec.type }}">
                                {% if rec.type == 'critical' %}🔴{% elif rec.type == 'optimization' %}🟡{% else %}🟢{% endif %}
                                {{ rec.message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% else %}
                <div class="loading">
                    <div class="spinner"></div>
                    <div>Verificación en progreso...</div>
                    <div style="margin-top: 20px; font-size: 0.9em;">
                        Esta página se actualizará automáticamente cuando termine la verificación.
                    </div>
                </div>
            {% endif %}
            <div class="nav-links">
                <a href="{{ url_for('index') }}">🏠 Inicio</a>
                <a href="{{ url_for('history') }}">📚 Historial</a>
                <a href="{{ url_for('run_check') }}" onclick="return confirm('¿Ejecutar nueva verificación?')">🔄 Nueva Verificación</a>
            </div>
        </div>
    </div>
    <script>
        // Auto-refresh si no hay resultados
        {% if not results %}
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        {% endif %}
    </script>
</body>
</html>"""

    # Guardar templates
    with open(
        templates_dir / "functionality_check_index.html", "w", encoding="utf-8"
    ) as f:
        f.write(index_html)  # pyright: ignore[reportUnusedCallResult]

    with open(templates_dir / "functionality_results.html", "w", encoding="utf-8") as f:
        f.write(results_html)  # pyright: ignore[reportUnusedCallResult]

    # Template de verificación en progreso
    progress_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación en Progreso - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 500px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        p {
            color: #7f8c8d;
            line-height: 1.6;
        }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #ecf0f1;
            border-radius: 5px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            animation: progress 2s ease-in-out infinite;
        }
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h1>🚀 Verificación en Progreso</h1>
        <p>Estamos verificando todas las funcionalidades de la aplicación...</p>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p>Esta página se actualizará automáticamente cuando termine la verificación.</p>
    </div>
    <script>
        // Auto-refresh cada 3 segundos
        setInterval(function() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (!data.check_in_progress) {
                        window.location.href = '/results';
                    }
                });
        }, 3000);
    </script>
</body>
</html>"""

    with open(templates_dir / "check_in_progress.html", "w", encoding="utf-8") as f:
        f.write(progress_html)  # pyright: ignore[reportUnusedCallResult]

    # Template de historial
    history_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial de Verificaciones - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 40px;
        }
        .history-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            transition: all 0.3s ease;
        }
        .history-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .history-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .history-date {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .history-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .history-stat {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        .history-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        .history-label {
            color: #7f8c8d;
            font-size: 0.8em;
        }
        .history-actions {
            margin-top: 15px;
            text-align: right;
        }
        .history-actions a {
            display: inline-block;
            padding: 8px 15px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        .history-actions a:hover {
            background: #2980b9;
        }
        .nav-links {
            margin-top: 30px;
            text-align: center;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #ecf0f1;
            color: #2c3e50;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #3498db;
            color: white;
        }
        .no-history {
            text-align: center;
            padding: 50px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Historial de Verificaciones</h1>
        </div>
        
        <div class="content">
            {% if history %}
                {% for item in history %}
                    <div class="history-item">
                        <div class="history-header">
                            <div class="history-title">{{ item.filename }}</div>
                            <div class="history-date">{{ item.timestamp[:19].replace('T', ' ') }}</div>
                        </div>
                        <div class="history-stats">
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.passed_checks }}/{{ item.summary.total_checks }}</div>
                                <div class="history-label">Verificaciones</div>
                            </div>
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.success_rate }}%</div>
                                <div class="history-label">Éxito</div>
                            </div>
                            <div class="history-stat">
                                <div class="history-number">{{ item.summary.overall_status }}</div>
                                <div class="history-label">Estado</div>
                            </div>
                        </div>
                        <div class="history-actions">
                            <a href="{{ url_for('view_result', filename=item.filename) }}">📊 Ver Detalles</a>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-history">
                    <h2>📭 No hay historial disponible</h2>
                    <p>Ejecuta tu primera verificación para crear historial.</p>
                </div>
            {% endif %}
            <div class="nav-links">
                <a href="{{ url_for('index') }}">🏠 Inicio</a>
                <a href="{{ url_for('run_check') }}">🚀 Nueva Verificación</a>
            </div>
        </div>
    </div>
</body>
</html>"""  # noqa: W293

    with open(templates_dir / "check_history.html", "w", encoding="utf-8") as f:
        f.write(history_html)  # pyright: ignore[reportUnusedCallResult]

    # Template de error
    error_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error en Verificación - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 600px;
        }
        .error-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 20px;
        }
        .error-message {
            background: #fadbd8;
            color: #721c24;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .nav-links {
            margin-top: 30px;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">❌</div>
        <h1>Error en la Verificación</h1>
        <p>Ocurrió un error durante la verificación de funcionalidad:</p>
        <div class="error-message">{{ error }}</div>
        <div class="nav-links">
            <a href="{{ url_for('index') }}">🏠 Volver al Inicio</a>
            <a href="{{ url_for('run_check') }}">🔄 Intentar de Nuevo</a>
        </div>
    </div>
</body>
</html>"""

    with open(templates_dir / "check_error.html", "w", encoding="utf-8") as f:
        f.write(error_html)  # pyright: ignore[reportUnusedCallResult]

    # Template de no historial
    no_history_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sin Historial - EDF_CatalogoDeTablas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 50px;
            text-align: center;
            max-width: 500px;
        }
        .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        p {
            color: #7f8c8d;
            line-height: 1.6;
        }
        .nav-links {
            margin-top: 30px;
        }
        .nav-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        .nav-links a:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📭</div>
        <h1>Sin Historial Disponible</h1>
        <p>No se encontraron archivos de verificación anteriores.</p>
        <p>Ejecuta tu primera verificación para crear historial.</p>
        <div class="nav-links">
            <a href="{{ url_for('index') }}">🏠 Volver al Inicio</a>
            <a href="{{ url_for('run_check') }}">🚀 Ejecutar Primera Verificación</a>
        </div>
    </div>
</body>
</html>"""

    with open(templates_dir / "no_history.html", "w", encoding="utf-8") as f:
        f.write(no_history_html)  # pyright: ignore[reportUnusedCallResult]
