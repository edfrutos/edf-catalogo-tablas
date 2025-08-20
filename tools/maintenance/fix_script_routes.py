#!/usr/bin/env python3
"""
Script para diagnosticar y corregir problemas de rutas de scripts
"""

import json
import os
import subprocess
import sys
from datetime import datetime

import requests


def check_blueprint_registration():
    """Verifica el registro de blueprints"""
    print("=== VERIFICACIÓN DE BLUEPRINTS ===")

    # Verificar qué archivos de rutas existen
    route_files = [
        "app/routes/scripts_routes.py",
        "app/routes/scripts_tools_routes.py",
        "app/routes/script_routes.py",
        "tools/app/routes/scripts_routes.py",
        "scripts/local/app/routes/scripts_routes.py"
    ]

    existing_files = []
    for file_path in route_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (no existe)")

    return existing_files

def test_script_runner():
    """Prueba el script_runner directamente"""
    print("\n=== PRUEBA DE SCRIPT_RUNNER ===")

    try:
        result = subprocess.run([
            sys.executable,
            "tools/script_runner.py",
            "tools/local/db_utils/conexion_MongoDB.py"
        ], capture_output=True, text=True, timeout=30)

        print("✅ script_runner ejecutado exitosamente")
        print(f"   Código de salida: {result.returncode}")

        if result.stdout:
            try:
                json_output = json.loads(result.stdout)
                print("   ✅ JSON válido recibido")
                return True
            except json.JSONDecodeError:
                print("   ❌ Error parseando JSON")
                print(f"   Salida: {result.stdout[:200]}...")
                return False

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_web_routes():
    """Prueba las rutas web"""
    print("\n=== PRUEBA DE RUTAS WEB ===")

    base_url = "http://127.0.0.1:8000"
    routes_to_test = [
        "/admin/tools/",
        "/admin/tools/execute",
        "/admin/scripts-tools-api/run"
    ]

    session = requests.Session()

    for route in routes_to_test:
        try:
            print(f"\nProbando: {route}")

            if route.endswith("/execute"):
                # POST request para execute
                response = session.post(
                    f"{base_url}{route}",
                    json={"script": "tools/local/db_utils/conexion_MongoDB.py"},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            elif route.endswith("/run"):
                # POST request para run
                response = session.post(
                    f"{base_url}{route}",
                    json={"path": "tools/local/db_utils/conexion_MongoDB.py"},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            else:
                # GET request para otras rutas
                response = session.get(f"{base_url}{route}", timeout=10)

            print(f"   Código: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    try:
                        json_response = response.json()
                        print("   ✅ Respuesta JSON válida")
                        return True
                    except:
                        print("   ❌ Error parseando JSON")
                else:
                    print("   ⚠️  Respuesta HTML (posiblemente página de login)")
            elif response.status_code == 302:
                redirect_location = response.headers.get('Location', '')
                print(f"   ⚠️  Redirección a: {redirect_location}")
            elif response.status_code == 401:
                print("   ❌ No autorizado")
            else:
                print(f"   ❌ Código inesperado: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    return False

def create_unified_script_route():
    """Crea una ruta unificada para scripts"""
    print("\n=== CREANDO RUTA UNIFICADA ===")

    # Crear un archivo de ruta unificada
    unified_route_content = '''#!/usr/bin/env python3
"""
Ruta unificada para ejecución de scripts
"""

import os
import subprocess
import json
from flask import Blueprint, jsonify, request, current_app
from app.decorators import admin_required

# Crear blueprint unificado
unified_scripts_bp = Blueprint("unified_scripts", __name__, url_prefix="/admin/tools")

@unified_scripts_bp.route("/execute", methods=["POST"])
@admin_required
def execute_script():
    """Ejecuta un script usando script_runner.py"""
    try:
        # Obtener datos del request
        if request.is_json:
            data = request.get_json()
            script_path = data.get("script") or data.get("script_path") or ""
        else:
            script_path = request.form.get("script") or request.form.get("script_path") or ""
        
        if not script_path:
            return jsonify({
                "error": "Ruta del script no proporcionada",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 400
        
        # Validar ruta
        if ".." in script_path or script_path.startswith("/"):
            return jsonify({
                "error": "Ruta no permitida",
                "script": script_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 400
        
        # Construir ruta absoluta
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_abs_path = os.path.join(project_root, script_path)
        
        if not os.path.exists(script_abs_path):
            return jsonify({
                "error": f"Script no encontrado: {script_path}",
                "script": script_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 404
        
        # Ejecutar usando script_runner
        script_runner_path = os.path.join(project_root, "tools", "script_runner.py")
        
        if not os.path.exists(script_runner_path):
            return jsonify({
                "error": "script_runner.py no encontrado",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
        
        # Ejecutar el script
        result = subprocess.run([
            sys.executable,
            script_runner_path,
            script_path
        ], capture_output=True, text=True, timeout=60, cwd=project_root)
        
        # Parsear la salida JSON del script_runner
        try:
            json_output = json.loads(result.stdout)
            return jsonify(json_output)
        except json.JSONDecodeError:
            # Si no es JSON válido, devolver error
            return jsonify({
                "error": "Error en la ejecución del script",
                "script": script_path,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "error": "Timeout en la ejecución del script",
            "script": script_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 408
    except Exception as e:
        return jsonify({
            "error": f"Error interno: {str(e)}",
            "script": script_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@unified_scripts_bp.route("/", methods=["GET"])
@admin_required
def tools_dashboard():
    """Página principal de herramientas"""
    return current_app.send_static_file("admin/tools_dashboard.html")
'''

    # Escribir el archivo
    with open("app/routes/unified_scripts_routes.py", "w") as f:
        f.write(unified_route_content)

    print("✅ Archivo unified_scripts_routes.py creado")
    return True

def update_app_registration():
    """Actualiza el registro de blueprints en la aplicación"""
    print("\n=== ACTUALIZANDO REGISTRO DE BLUEPRINTS ===")

    # Leer el archivo main_app.py
    main_app_path = "main_app.py"
    if not os.path.exists(main_app_path):
        print(f"❌ {main_app_path} no encontrado")
        return False

    with open(main_app_path) as f:
        content = f.read()

    # Buscar y reemplazar el registro de scripts_bp
    if "scripts_bp" in content:
        # Comentar el registro existente
        content = content.replace(
            "app.register_blueprint(scripts_bp)",
            "# app.register_blueprint(scripts_bp)  # Comentado para usar unified_scripts_bp"
        )

        # Agregar el nuevo registro
        content = content.replace(
            "# Registrar rutas de mantenimiento y API usando la función dedicada",
            "# Registrar rutas de mantenimiento y API usando la función dedicada\n    from app.routes.unified_scripts_routes import unified_scripts_bp\n    app.register_blueprint(unified_scripts_bp)"
        )

        # Escribir el archivo actualizado
        with open(main_app_path, "w") as f:
            f.write(content)

        print("✅ main_app.py actualizado")
        return True
    else:
        print("❌ No se encontró scripts_bp en main_app.py")
        return False

def restart_server():
    """Reinicia el servidor"""
    print("\n=== REINICIANDO SERVIDOR ===")

    try:
        result = subprocess.run(["systemctl", "restart", "edefrutos2025"],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Servidor reiniciado exitosamente")
            return True
        else:
            print(f"❌ Error reiniciando servidor: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 DIAGNÓSTICO Y CORRECCIÓN DE RUTAS DE SCRIPTS")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Verificaciones
    print("\n1. Verificando blueprints existentes...")
    existing_files = check_blueprint_registration()

    print("\n2. Probando script_runner...")
    script_runner_ok = test_script_runner()

    print("\n3. Probando rutas web...")
    web_routes_ok = test_web_routes()

    # Si hay problemas, aplicar correcciones
    if not web_routes_ok:
        print("\n🔧 APLICANDO CORRECCIONES...")

        print("\n4. Creando ruta unificada...")
        create_unified_script_route()

        print("\n5. Actualizando registro de blueprints...")
        update_app_registration()

        print("\n6. Reiniciando servidor...")
        restart_server()

        # Esperar un momento y probar de nuevo
        import time
        time.sleep(5)

        print("\n7. Probando rutas después de las correcciones...")
        web_routes_ok = test_web_routes()

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)

    print(f"✅ Script Runner: {'OK' if script_runner_ok else 'ERROR'}")
    print(f"✅ Rutas Web: {'OK' if web_routes_ok else 'ERROR'}")

    if script_runner_ok and web_routes_ok:
        print("\n🎉 ¡Todas las correcciones aplicadas exitosamente!")
        print("El sistema de scripts debería funcionar correctamente ahora.")
    else:
        print("\n⚠️  Algunos problemas persisten.")
        print("Revisar los errores anteriores para más detalles.")

    return script_runner_ok and web_routes_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
