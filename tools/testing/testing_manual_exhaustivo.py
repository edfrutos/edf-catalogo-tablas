#!/usr/bin/env python3
"""
Testing Manual Exhaustivo - EDF CatálogoDeTablas
================================================

Este script ejecuta el testing manual siguiendo el plan exhaustivo
definido en docs/testing/PLAN_TESTING_EXHAUSTIVO.md
"""

import json
import os
import sys
import time
from datetime import datetime

import requests


class TestingManualExhaustivo:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.session = requests.Session()
        self.results = []
        self.start_time = datetime.now()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_endpoint(self, endpoint, expected_status=200, description=""):
        """Testea un endpoint específico"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, timeout=10)
            status = response.status_code
            success = status == expected_status

            result = {
                "endpoint": endpoint,
                "status": status,
                "expected": expected_status,
                "success": success,
                "description": description,
            }

            if success:
                self.log(f"✅ {endpoint} - {status} {description}")
            else:
                self.log(
                    f"❌ {endpoint} - {status} (esperado: {expected_status}) {description}"
                )

            self.results.append(result)
            return success

        except Exception as e:
            self.log(f"❌ {endpoint} - Error: {str(e)}", "ERROR")
            self.results.append(
                {
                    "endpoint": endpoint,
                    "status": "ERROR",
                    "expected": expected_status,
                    "success": False,
                    "description": f"Error: {str(e)}",
                }
            )
            return False

    def test_infrastructure(self):
        """Fase 1: Testing de Infraestructura"""
        self.log("🔧 FASE 1: Testing de Infraestructura")
        self.log("=" * 50)

        # 1.1 Verificar que el servidor esté funcionando
        self.log("1.1 Verificando servidor...")
        self.test_endpoint("/", 200, "Página principal")

        # 1.2 Verificar archivos estáticos
        self.log("1.2 Verificando archivos estáticos...")
        self.test_endpoint("/static/css/styles.css", 200, "CSS principal")
        self.test_endpoint("/static/js/dashboard.js", 200, "JavaScript principal")
        self.test_endpoint("/static/favicon.ico", 200, "Favicon")

        # 1.3 Verificar rutas de autenticación
        self.log("1.3 Verificando rutas de autenticación...")
        self.test_endpoint("/login", 200, "Página de login")
        self.test_endpoint("/register", 200, "Página de registro")
        self.test_endpoint("/logout", 302, "Logout (redirect)")

        # 1.4 Verificar rutas de error
        self.log("1.4 Verificando rutas de error...")
        self.test_endpoint("/nonexistent", 404, "Página 404")

    def test_database_operations(self):
        """Fase 2: Testing de Operaciones de Base de Datos"""
        self.log("\n🗄️ FASE 2: Testing de Base de Datos")
        self.log("=" * 50)

        # 2.1 Verificar conexión a MongoDB
        self.log("2.1 Verificando conexión a MongoDB...")
        self.test_endpoint("/api/health", 200, "Health check de base de datos")

        # 2.2 Verificar operaciones CRUD básicas
        self.log("2.2 Verificando operaciones CRUD...")
        self.test_endpoint("/api/catalogs", 200, "Listar catálogos")

    def test_image_operations(self):
        """Fase 3: Testing de Operaciones de Imágenes"""
        self.log("\n🖼️ FASE 3: Testing de Imágenes")
        self.log("=" * 50)

        # 3.1 Verificar rutas de imágenes
        self.log("3.1 Verificando rutas de imágenes...")
        self.test_endpoint("/static/default_profile.png", 200, "Imagen por defecto")

        # 3.2 Verificar subida de imágenes (sin archivo)
        self.log("3.2 Verificando subida de imágenes...")
        self.test_endpoint("/upload", 405, "Subida de imágenes (método no permitido)")

    def test_security(self):
        """Fase 4: Testing de Seguridad"""
        self.log("\n🔒 FASE 4: Testing de Seguridad")
        self.log("=" * 50)

        # 4.1 Verificar rutas protegidas
        self.log("4.1 Verificando rutas protegidas...")
        self.test_endpoint("/admin", 302, "Panel admin (redirect a login)")
        self.test_endpoint("/dashboard", 302, "Dashboard (redirect a login)")

        # 4.2 Verificar headers de seguridad
        self.log("4.2 Verificando headers de seguridad...")
        response = self.session.get(f"{self.base_url}/", timeout=10)
        headers = response.headers

        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
        }

        for header, expected_value in security_headers.items():
            if header in headers:
                self.log(f"✅ {header}: {headers[header]}")
            else:
                self.log(f"⚠️ {header}: No encontrado", "WARNING")

    def test_specific_functionalities(self):
        """Fase 5: Testing de Funcionalidades Específicas"""
        self.log("\n⚙️ FASE 5: Testing de Funcionalidades Específicas")
        self.log("=" * 50)

        # 5.1 Verificar rutas de catálogos
        self.log("5.1 Verificando rutas de catálogos...")
        self.test_endpoint("/catalogs", 302, "Lista de catálogos (redirect)")
        self.test_endpoint("/catalogs/create", 302, "Crear catálogo (redirect)")

        # 5.2 Verificar rutas de mantenimiento
        self.log("5.2 Verificando rutas de mantenimiento...")
        self.test_endpoint("/maintenance", 302, "Panel de mantenimiento (redirect)")
        self.test_endpoint("/api/maintenance/status", 200, "Estado de mantenimiento")

        # 5.3 Verificar rutas de herramientas
        self.log("5.3 Verificando rutas de herramientas...")
        self.test_endpoint("/tools", 302, "Panel de herramientas (redirect)")

    def test_ui_responsiveness(self):
        """Fase 6: Testing de UI y Responsividad"""
        self.log("\n📱 FASE 6: Testing de UI y Responsividad")
        self.log("=" * 50)

        # 6.1 Verificar contenido HTML
        self.log("6.1 Verificando contenido HTML...")
        response = self.session.get(f"{self.base_url}/", timeout=10)
        content = response.text.lower()

        # Verificar elementos básicos
        checks = [
            ("title", "title" in content),
            ("meta", "meta" in content),
            ("css", "styles.css" in content),
            ("javascript", "dashboard.js" in content),
        ]

        for element, found in checks:
            if found:
                self.log(f"✅ Elemento {element} encontrado")
            else:
                self.log(f"❌ Elemento {element} no encontrado")

    def test_performance(self):
        """Fase 7: Testing de Rendimiento"""
        self.log("\n⚡ FASE 7: Testing de Rendimiento")
        self.log("=" * 50)

        # 7.1 Medir tiempo de respuesta
        self.log("7.1 Mediendo tiempos de respuesta...")

        endpoints = ["/", "/login", "/register", "/static/css/styles.css"]

        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # en ms

                if response_time < 1000:  # menos de 1 segundo
                    self.log(f"✅ {endpoint}: {response_time:.2f}ms")
                else:
                    self.log(f"⚠️ {endpoint}: {response_time:.2f}ms (lento)", "WARNING")

            except Exception as e:
                self.log(f"❌ {endpoint}: Error - {str(e)}", "ERROR")

    def test_integration(self):
        """Fase 8: Testing de Integración"""
        self.log("\n🔗 FASE 8: Testing de Integración")
        self.log("=" * 50)

        # 8.1 Verificar integración con servicios externos
        self.log("8.1 Verificando integración con servicios...")

        # Verificar configuración de AWS S3
        self.test_endpoint("/api/config/s3", 200, "Configuración S3")

        # Verificar configuración de Google Drive
        self.test_endpoint("/api/config/drive", 200, "Configuración Google Drive")

    def test_edge_cases(self):
        """Fase 9: Testing de Casos Extremos"""
        self.log("\n🎯 FASE 9: Testing de Casos Extremos")
        self.log("=" * 50)

        # 9.1 Verificar URLs malformadas
        self.log("9.1 Verificando URLs malformadas...")
        self.test_endpoint("/%20", 404, "URL con espacios")
        self.test_endpoint("/..", 404, "Path traversal")
        self.test_endpoint("/'", 404, "URL con comillas")

        # 9.2 Verificar métodos HTTP no soportados
        self.log("9.2 Verificando métodos HTTP...")
        try:
            response = self.session.post(f"{self.base_url}/", timeout=10)
            self.log(f"✅ POST /: {response.status_code}")
        except Exception as e:
            self.log(f"❌ POST /: Error - {str(e)}", "ERROR")

    def generate_report(self):
        """Genera el reporte final"""
        self.log("\n📊 GENERANDO REPORTE FINAL")
        self.log("=" * 50)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        self.log(f"Total de tests: {total_tests}")
        self.log(f"Tests pasados: {passed_tests}")
        self.log(f"Tests fallidos: {failed_tests}")
        self.log(f"Tasa de éxito: {success_rate:.1f}%")

        # Guardar reporte en archivo
        report_file = (
            f"testing_manual_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": self.start_time.isoformat(),
                    "duration": str(datetime.now() - self.start_time),
                    "summary": {
                        "total": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "success_rate": success_rate,
                    },
                    "results": self.results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        self.log(f"Reporte guardado en: {report_file}")

        if success_rate >= 90:
            self.log("🎉 ¡EXCELENTE! La aplicación está funcionando correctamente")
        elif success_rate >= 70:
            self.log("✅ BUENO - Algunos problemas menores detectados")
        else:
            self.log("⚠️ PROBLEMAS DETECTADOS - Revisar errores")

    def run_all_tests(self):
        """Ejecuta todos los tests"""
        self.log("🧪 INICIANDO TESTING MANUAL EXHAUSTIVO")
        self.log("=" * 60)
        self.log(f"URL base: {self.base_url}")
        self.log(f"Hora de inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 60)

        try:
            self.test_infrastructure()
            self.test_database_operations()
            self.test_image_operations()
            self.test_security()
            self.test_specific_functionalities()
            self.test_ui_responsiveness()
            self.test_performance()
            self.test_integration()
            self.test_edge_cases()

        except KeyboardInterrupt:
            self.log("Testing interrumpido por el usuario", "WARNING")
        except Exception as e:
            self.log(f"Error durante el testing: {str(e)}", "ERROR")

        self.generate_report()


def main():
    """Función principal"""
    print("🧪 Testing Manual Exhaustivo - EDF CatálogoDeTablas")
    print("=" * 60)

    # Verificar que el servidor esté ejecutándose
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Flask ejecutándose en puerto 5001")
        else:
            print(f"⚠️ Servidor respondiendo con código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {str(e)}")
        print("💡 Asegúrate de que el servidor Flask esté ejecutándose en puerto 5001")
        return

    # Ejecutar tests
    tester = TestingManualExhaustivo()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
