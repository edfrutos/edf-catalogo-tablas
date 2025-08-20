#!/usr/bin/env python3
"""
🧪 Script de Testing Automatizado - EDF CatálogoDeTablas
Ejecuta pruebas básicas para detectar bugs comunes
"""

import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests

# Configuración
BASE_URL = "http://localhost:5001"
TEST_TIMEOUT = 30
APP_NAME = "EDF_CatalogoDeTablas"


class TestRunner:
    def __init__(self):
        self.results = []
        self.errors = []
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_environment(self) -> bool:
        """Test 1: Verificar entorno de desarrollo"""
        self.log("🔍 Verificando entorno de desarrollo...")

        checks = [
            ("Entorno virtual", "VIRTUAL_ENV" in os.environ),
            ("Flask instalado", self._check_flask_installed()),
            ("Puerto 5001 libre", self._check_port_5001()),
            ("Archivo wsgi.py", os.path.exists("wsgi.py")),
            ("Archivo config.py", os.path.exists("config.py")),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            self.log(f"   {status} {check_name}")
            if not passed:
                all_passed = False

        return all_passed

    def _check_flask_installed(self) -> bool:
        try:
            import flask

            return True
        except ImportError:
            return False

    def _check_port_5001(self) -> bool:
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", 5001))
            sock.close()
            return result != 0  # Puerto libre si no se puede conectar
        except:
            return False

    def test_server_startup(self) -> bool:
        """Test 2: Verificar que el servidor puede iniciar"""
        self.log("🚀 Verificando inicio del servidor...")

        try:
            # Configurar variables de entorno para el test
            env = os.environ.copy()
            env.update(
                {"FLASK_ENV": "development", "FLASK_DEBUG": "1", "FLASK_APP": "wsgi.py"}
            )

            # Intentar iniciar el servidor en background usando el entorno virtual
            process = subprocess.Popen(
                [
                    ".venv/bin/python",
                    "-m",
                    "flask",
                    "run",
                    "--debug",
                    "--port=5001",
                    "--host=0.0.0.0",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            # Esperar un poco para que inicie
            time.sleep(5)

            # Verificar si el proceso sigue ejecutándose
            if process.poll() is None:
                self.log("✅ Servidor iniciado correctamente")
                # Terminar el proceso
                process.terminate()
                process.wait()
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ Error iniciando servidor: {stderr.decode()}")
                return False

        except Exception as e:
            self.log(f"❌ Error en test de servidor: {e}")
            return False

    def test_basic_routes(self) -> bool:
        """Test 3: Verificar rutas básicas"""
        self.log("🌐 Verificando rutas básicas...")

        # Configurar variables de entorno para el test
        env = os.environ.copy()
        env.update(
            {"FLASK_ENV": "development", "FLASK_DEBUG": "1", "FLASK_APP": "wsgi.py"}
        )

        # Iniciar servidor en background usando el entorno virtual
        process = subprocess.Popen(
            [
                ".venv/bin/python",
                "-m",
                "flask",
                "run",
                "--debug",
                "--port=5001",
                "--host=0.0.0.0",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Esperar a que el servidor esté listo
            time.sleep(8)

            routes_to_test = [
                ("/", "Página principal"),
                ("/login", "Página de login"),
                ("/register", "Página de registro"),
                ("/static/css/styles.css", "CSS principal"),
            ]

            all_passed = True
            for route, description in routes_to_test:
                try:
                    response = requests.get(f"{BASE_URL}{route}", timeout=5)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {status} {description} ({response.status_code})")
                    if response.status_code != 200:
                        all_passed = False
                except requests.exceptions.RequestException as e:
                    self.log(f"   ❌ {description} (Error: {e})")
                    all_passed = False

            return all_passed

        finally:
            # Terminar el servidor
            process.terminate()
            process.wait()

    def test_database_connection(self) -> bool:
        """Test 4: Verificar conexión a base de datos"""
        self.log("🗄️ Verificando conexión a base de datos...")

        try:
            # Agregar el directorio actual al path para imports
            import sys

            sys.path.insert(0, os.getcwd())

            from app.models.database import get_mongo_client, get_mongo_db

            client = get_mongo_client()
            db = get_mongo_db()

            # Intentar una operación simple
            collections = db.list_collection_names()

            self.log(f"✅ Conexión a MongoDB exitosa ({len(collections)} colecciones)")
            return True

        except Exception as e:
            self.log(f"❌ Error de conexión a MongoDB: {e}")
            return False

    def test_file_structure(self) -> bool:
        """Test 5: Verificar estructura de archivos"""
        self.log("📁 Verificando estructura de archivos...")

        required_files = [
            "app/__init__.py",
            "app/models/__init__.py",
            "app/routes/__init__.py",
            "app/templates/base.html",
            "app/static/css/styles.css",
            "config.py",
            "wsgi.py",
            "requirements_python310.txt",
        ]

        all_passed = True
        for file_path in required_files:
            exists = os.path.exists(file_path)
            status = "✅" if exists else "❌"
            self.log(f"   {status} {file_path}")
            if not exists:
                all_passed = False

        return all_passed

    def test_imports(self) -> bool:
        """Test 6: Verificar imports críticos"""
        self.log("📦 Verificando imports críticos...")

        critical_modules = [
            "flask",
            "flask_login",
            "flask_session",
            "pymongo",
            "dotenv",
            "werkzeug",
            "openpyxl",
            "boto3",
        ]

        all_passed = True
        for module in critical_modules:
            try:
                __import__(module)
                self.log(f"   ✅ {module}")
            except ImportError as e:
                self.log(f"   ❌ {module} ({e})")
                all_passed = False

        return all_passed

    def test_configuration(self) -> bool:
        """Test 7: Verificar configuración"""
        self.log("⚙️ Verificando configuración...")

        try:
            # Agregar el directorio actual al path para imports
            import sys

            sys.path.insert(0, os.getcwd())

            from config import Config

            config = Config()

            checks = [
                ("SECRET_KEY", hasattr(config, "SECRET_KEY") and config.SECRET_KEY),
                ("MONGO_URI", hasattr(config, "MONGO_URI") and config.MONGO_URI),
                ("UPLOAD_FOLDER", hasattr(config, "UPLOAD_FOLDER")),
                ("SESSION_TYPE", hasattr(config, "SESSION_TYPE")),
            ]

            all_passed = True
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                self.log(f"   {status} {check_name}")
                if not passed:
                    all_passed = False

            return all_passed

        except Exception as e:
            self.log(f"❌ Error verificando configuración: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Ejecutar todos los tests"""
        self.log("🧪 Iniciando testing exhaustivo...")
        self.log("=" * 50)

        tests = [
            ("Entorno de desarrollo", self.test_environment),
            ("Inicio del servidor", self.test_server_startup),
            ("Rutas básicas", self.test_basic_routes),
            ("Conexión a base de datos", self.test_database_connection),
            ("Estructura de archivos", self.test_file_structure),
            ("Imports críticos", self.test_imports),
            ("Configuración", self.test_configuration),
        ]

        results = {}

        for test_name, test_func in tests:
            self.log(f"\n🔍 Ejecutando: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASÓ" if result else "❌ FALLÓ"
                self.log(f"Resultado: {status}")
            except Exception as e:
                self.log(f"❌ Error en {test_name}: {e}")
                results[test_name] = False

        return results

    def generate_report(self, results: Dict[str, bool]):
        """Generar reporte de testing"""
        self.log("\n" + "=" * 50)
        self.log("📊 REPORTE DE TESTING")
        self.log("=" * 50)

        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests

        self.log(f"Total de tests: {total_tests}")
        self.log(f"Tests pasados: {passed_tests}")
        self.log(f"Tests fallidos: {failed_tests}")
        self.log(f"Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            self.log("\n❌ TESTS FALLIDOS:")
            for test_name, result in results.items():
                if not result:
                    self.log(f"   - {test_name}")

        self.log("\n✅ TESTS EXITOSOS:")
        for test_name, result in results.items():
            if result:
                self.log(f"   - {test_name}")

        # Recomendaciones
        self.log("\n💡 RECOMENDACIONES:")
        if failed_tests == 0:
            self.log("   🎉 ¡Excelente! La aplicación está lista para testing manual.")
            self.log(
                "   📋 Ejecuta el plan de testing manual para verificar funcionalidades específicas."
            )
        else:
            self.log("   🔧 Corrige los errores encontrados antes de continuar.")
            self.log("   📋 Revisa los logs para más detalles.")

        # Guardar reporte
        report_file = f"testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write(f"Reporte de Testing - {APP_NAME}\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(
                f"Total: {total_tests}, Pasados: {passed_tests}, Fallidos: {failed_tests}\n\n"
            )

            for test_name, result in results.items():
                f.write(f"{'✅' if result else '❌'} {test_name}\n")

        self.log(f"\n📄 Reporte guardado en: {report_file}")


def main():
    """Función principal"""
    print("🧪 Testing Automatizado - EDF CatálogoDeTablas")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not os.path.exists("wsgi.py"):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        sys.exit(1)

    # Crear y ejecutar tests
    runner = TestRunner()
    results = runner.run_all_tests()
    runner.generate_report(results)

    # Código de salida
    failed_tests = sum(1 for result in results.values() if not result)
    sys.exit(failed_tests)


if __name__ == "__main__":
    main()
