#!/usr/bin/env python3
"""
Script de Verificación de Funcionalidad - EDF_CatalogoDeTablas
Verifica todas las funcionalidades de la aplicación después de la limpieza de dependencias

Autor: Sistema de verificación automática
Fecha: 2025-08-27
Python: 3.10+
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple  # pyright: ignore[reportUnusedImport]
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/functionality_check.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AppFunctionalityChecker:
    """Clase para verificar la funcionalidad completa de la aplicación"""

    def __init__(self):  # pyright: ignore[reportMissingSuperCall]
        self.project_root = Path.cwd()
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "checks": {},
            "summary": {},
            "recommendations": [],
        }

    def check_python_version(self) -> bool:
        """Verificar versión de Python"""
        version = sys.version_info
        is_compatible = version.major == 3 and version.minor == 10

        self.results["checks"]["python_version"] = {
            "status": "✅" if is_compatible else "❌",
            "current": f"{version.major}.{version.minor}.{version.micro}",
            "required": "3.10.x",
            "compatible": is_compatible,
        }

        logger.info(
            f"Python {version.major}.{version.minor}.{version.micro} - {'✅ Compatible' if is_compatible else '❌ Incompatible'}"
        )
        return is_compatible

    def check_dependencies(self) -> Dict[str, Any]:
        """Verificar dependencias críticas"""
        dependencies = {
            "flask": "Flask",
            "pymongo": "MongoDB",
            "boto3": "AWS S3",
            "pandas": "Pandas",
            "pytest": "Pytest",
        }

        results = {}
        all_working = True

        for package, display_name in dependencies.items():
            try:
                __import__(package)
                results[package] = {
                    "status": "✅",
                    "working": True,
                    "name": display_name,
                }
                logger.info(f"✅ {display_name} funciona correctamente")
            except ImportError as e:
                results[package] = {
                    "status": "❌",
                    "working": False,
                    "name": display_name,
                    "error": str(e),
                }
                all_working = False
                logger.error(f"❌ {display_name} no funciona: {e}")

        self.results["checks"]["dependencies"] = results
        return {"working": all_working, "total": len(dependencies)}

    def check_flask_app_creation(self) -> Dict[str, Any]:
        """Verificar creación de la aplicación Flask"""
        try:
            # Cambiar al directorio del proyecto
            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            # Importar y crear la aplicación
            sys.path.insert(0, str(self.project_root))
            from app import create_app

            start_time = time.time()
            app = create_app()
            creation_time = time.time() - start_time

            # Verificar que la aplicación se creó correctamente
            if app and hasattr(app, "url_map"):
                routes_count = len(list(app.url_map.iter_rules()))

                # Categorizar rutas
                api_routes = len(
                    [r for r in app.url_map.iter_rules() if r.rule.startswith("/api")]
                )
                admin_routes = len(
                    [r for r in app.url_map.iter_rules() if r.rule.startswith("/admin")]
                )
                user_routes = len(
                    [
                        r
                        for r in app.url_map.iter_rules()
                        if not r.rule.startswith("/admin")
                        and not r.rule.startswith("/api")
                        and not r.rule.startswith("/static")
                    ]
                )

                result = {
                    "status": "✅",
                    "working": True,
                    "creation_time": round(creation_time, 3),
                    "total_routes": routes_count,
                    "api_routes": api_routes,
                    "admin_routes": admin_routes,
                    "user_routes": user_routes,
                }

                logger.info(f"✅ Aplicación Flask creada en {creation_time:.3f}s")
                logger.info(f"   - Total rutas: {routes_count}")
                logger.info(f"   - API routes: {api_routes}")
                logger.info(f"   - Admin routes: {admin_routes}")
                logger.info(f"   - User routes: {user_routes}")

            else:
                result = {
                    "status": "❌",
                    "working": False,
                    "error": "Aplicación no se creó correctamente",
                }
                logger.error("❌ Aplicación Flask no se creó correctamente")

            # Restaurar directorio original
            os.chdir(original_cwd)

        except Exception as e:
            result = {"status": "❌", "working": False, "error": str(e)}
            logger.error(f"❌ Error creando aplicación Flask: {e}")

        self.results["checks"]["flask_app"] = result
        return result

    def check_mongodb_connection(self) -> Dict[str, Any]:
        """Verificar conexión a MongoDB"""
        try:
            from app.database import get_mongo_db

            db = get_mongo_db()
            if db is not None:
                # Listar colecciones
                collections = db.list_collection_names()

                result = {
                    "status": "✅",
                    "working": True,
                    "collections_count": len(collections),
                    "collections": collections[:10],  # Primeras 10 colecciones
                }

                logger.info(f"✅ MongoDB conectado - {len(collections)} colecciones")

            else:
                result = {
                    "status": "❌",
                    "working": False,
                    "error": "No se pudo obtener la base de datos",
                }
                logger.error("❌ No se pudo conectar a MongoDB")

        except Exception as e:
            result = {"status": "❌", "working": False, "error": str(e)}
            logger.error(f"❌ Error conectando a MongoDB: {e}")

        self.results["checks"]["mongodb"] = result
        return result

    def check_aws_s3_connection(self) -> Dict[str, Any]:
        """Verificar conexión a AWS S3"""
        try:
            import boto3  # pyright: ignore[reportMissingTypeStubs]

            boto3.client("s3")  # pyright: ignore[reportUnusedCallResult]

            result = {"status": "✅", "working": True, "client_created": True}

            logger.info("✅ AWS S3 cliente creado correctamente")

        except Exception as e:
            result = {
                "status": "⚠️",
                "working": False,
                "error": str(e),
                "note": "S3 puede no estar configurado pero no es crítico",
            }
            logger.warning(f"⚠️ AWS S3 no disponible: {e}")

        self.results["checks"]["aws_s3"] = result
        return result

    def check_package_count(self) -> Dict[str, Any]:
        """Verificar número de paquetes instalados"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages = [
                line for line in result.stdout.strip().split("\n") if "==" in line
            ]
            package_count = len(packages)

            result_data = {
                "status": "✅",
                "working": True,
                "package_count": package_count,
                "optimized": package_count
                < 200,  # Considerar optimizado si menos de 200 paquetes
            }

            logger.info(f"✅ {package_count} paquetes instalados")

        except Exception as e:
            result_data = {"status": "❌", "working": False, "error": str(e)}
            logger.error(f"❌ Error contando paquetes: {e}")

        self.results["checks"]["package_count"] = result_data
        return result_data

    def check_environment_size(self) -> Dict[str, Any]:
        """Verificar tamaño del entorno virtual"""
        try:
            venv_path = self.project_root / ".venv"
            if venv_path.exists():
                # Usar du para obtener tamaño (macOS/Linux)
                result = subprocess.run(
                    ["du", "-sh", str(venv_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                size_str = result.stdout.strip().split("\t")[0]

                # Convertir a MB para comparación
                if "M" in size_str:
                    size_mb = float(size_str.replace("M", ""))
                elif "G" in size_str:
                    size_mb = float(size_str.replace("G", "")) * 1024
                else:
                    size_mb = float(size_str) / 1024

                result_data = {
                    "status": "✅",
                    "working": True,
                    "size": size_str,
                    "size_mb": round(size_mb, 1),
                    "optimized": size_mb
                    < 500,  # Considerar optimizado si menos de 500MB
                }

                logger.info(f"✅ Entorno virtual: {size_str}")

            else:
                result_data = {
                    "status": "⚠️",
                    "working": False,
                    "note": "Entorno virtual .venv no encontrado",
                }
                logger.warning("⚠️ Entorno virtual .venv no encontrado")

        except Exception as e:
            result_data = {"status": "❌", "working": False, "error": str(e)}
            logger.error(f"❌ Error verificando tamaño del entorno: {e}")

        self.results["checks"]["environment_size"] = result_data
        return result_data

    def generate_summary(self):
        """Generar resumen de todas las verificaciones"""
        checks = self.results["checks"]

        total_checks = len(checks)
        passed_checks = sum(
            1 for check in checks.values() if check.get("working", False)
        )
        critical_checks = sum(
            1
            for check in checks.values()
            if check.get("working", False) and check.get("status") == "✅"
        )

        # Calcular porcentaje de éxito
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        # Determinar estado general
        if success_rate >= 90:
            overall_status = "✅ EXCELENTE"
        elif success_rate >= 75:
            overall_status = "✅ BUENO"
        elif success_rate >= 50:
            overall_status = "⚠️ REGULAR"
        else:
            overall_status = "❌ CRÍTICO"

        self.results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "critical_checks": critical_checks,
            "success_rate": round(success_rate, 1),
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"📊 Resumen: {passed_checks}/{total_checks} verificaciones exitosas ({success_rate:.1f}%)"
        )
        logger.info(f"🎯 Estado general: {overall_status}")

    def generate_recommendations(self):
        """Generar recomendaciones basadas en los resultados"""
        recommendations = []
        checks = self.results["checks"]

        # Verificar Python
        if not checks.get("python_version", {}).get("compatible", False):
            recommendations.append(
                {
                    "type": "critical",
                    "message": "Actualizar a Python 3.10 para compatibilidad completa",
                }
            )

        # Verificar dependencias
        deps = checks.get("dependencies", {})
        if not deps.get("working", True):
            recommendations.append(
                {
                    "type": "critical",
                    "message": "Reinstalar dependencias críticas que fallaron",
                }
            )

        # Verificar aplicación Flask
        flask_check = checks.get("flask_app", {})
        if not flask_check.get("working", False):
            recommendations.append(
                {
                    "type": "critical",
                    "message": "Revisar configuración de la aplicación Flask",
                }
            )

        # Verificar MongoDB
        mongo_check = checks.get("mongodb", {})
        if not mongo_check.get("working", False):
            recommendations.append(
                {
                    "type": "critical",
                    "message": "Verificar conexión a MongoDB y configuración",
                }
            )

        # Verificar optimización
        pkg_check = checks.get("package_count", {})
        if not pkg_check.get("optimized", False):
            recommendations.append(
                {
                    "type": "optimization",
                    "message": "Considerar limpieza adicional de dependencias",
                }
            )

        env_check = checks.get("environment_size", {})
        if not env_check.get("optimized", False):
            recommendations.append(
                {
                    "type": "optimization",
                    "message": "El entorno virtual es grande, considerar optimización",
                }
            )

        # Recomendaciones positivas
        if all(check.get("working", False) for check in checks.values()):
            recommendations.append(
                {
                    "type": "success",
                    "message": "¡Todas las verificaciones pasaron! La aplicación está lista para producción",
                }
            )

        self.results["recommendations"] = recommendations

    def save_results(self) -> str:
        """Guardar resultados en archivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"functionality_check_{timestamp}.json"
        filepath = self.logs_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Resultados guardados en: {filepath}")
        return str(filepath)

    def run_all_checks(self) -> Dict[str, Any]:
        """Ejecutar todas las verificaciones"""
        logger.info("🚀 Iniciando verificación completa de funcionalidad")

        # Ejecutar verificaciones
        self.check_python_version()  # pyright: ignore[reportUnusedCallResult]
        self.check_dependencies()  # pyright: ignore[reportUnusedCallResult]
        self.check_flask_app_creation()  # pyright: ignore[reportUnusedCallResult]
        self.check_mongodb_connection()  # pyright: ignore[reportUnusedCallResult]
        self.check_aws_s3_connection()  # pyright: ignore[reportUnusedCallResult]
        self.check_package_count()  # pyright: ignore[reportUnusedCallResult]
        self.check_environment_size()  # pyright: ignore[reportUnusedCallResult]

        # Generar resumen y recomendaciones
        self.generate_summary()
        self.generate_recommendations()

        # Guardar resultados
        results_file = self.save_results()

        logger.info("✅ Verificación completa finalizada")

        return {"results": self.results, "results_file": results_file}


def main():
    """Función principal"""
    try:
        checker = AppFunctionalityChecker()
        results = checker.run_all_checks()

        # Mostrar resumen en consola
        summary = results["results"]["summary"]
        print("\n🎯 RESUMEN DE VERIFICACIÓN")
        print(f"   Estado general: {summary['overall_status']}")
        print(
            f"   Verificaciones exitosas: {summary['passed_checks']}/{summary['total_checks']}"
        )
        print(f"   Tasa de éxito: {summary['success_rate']}%")
        print(f"   Archivo de resultados: {results['results_file']}")

        # Mostrar recomendaciones
        recommendations = results["results"]["recommendations"]
        if recommendations:
            print("\n💡 RECOMENDACIONES:")
            for rec in recommendations:
                icon = (
                    "🔴"
                    if rec["type"] == "critical"
                    else "🟡" if rec["type"] == "optimization" else "🟢"
                )
                print(f"   {icon} {rec['message']}")

        return results

    except Exception as e:
        logger.error(f"❌ Error durante la verificación: {e}")
        print(f"\n❌ Error durante la verificación: {e}")
        return None


if __name__ == "__main__":
    main()  # pyright: ignore[reportUnusedCallResult]
