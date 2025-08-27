#!/usr/bin/env python3
"""
Script de limpieza de dependencias para Python 3.10
Elimina dependencias redundantes e incompatibles del proyecto EDF_CatalogoDeTablas

Autor: Sistema de limpieza automática
Fecha: 2025-08-27
Python: 3.10+
"""

import os  # pyright: ignore[reportUnusedImport]
import sys
import subprocess
import json
import shutil  # pyright: ignore[reportUnusedImport]
from pathlib import Path
from typing import List, Dict, Set, Tuple  # pyright: ignore[reportUnusedImport]
import logging


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dependency_cleanup.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DependencyCleaner:
    """Clase para limpiar dependencias del proyecto"""

    def __init__(self):  # pyright: ignore[reportMissingSuperCall]
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Dependencias problemáticas identificadas
        self.redundant_packages = {
            # Frameworks web duplicados
            "fastapi": "Conflicto con Flask",
            "starlette": "Parte de FastAPI, no necesario",
            "uvicorn": "Servidor ASGI, no necesario con Flask",
            # Interfaces gráficas duplicadas
            "PySide6": "Conflicto con PyQt6",
            "PySide6_Addons": "Parte de PySide6",
            "PySide6_Essentials": "Parte de PySide6",
            "shiboken6": "Parte de PySide6",
            # Herramientas de desarrollo duplicadas
            "pyright": "Type checker alternativo a mypy",
            "debugger": "Debugger redundante con debugpy",
            "print": "Utilidad innecesaria",
            "prettier": "Utilidad innecesaria",
            # Utilidades HTTP redundantes
            "httpx": "Cliente HTTP async, no necesario",
            "httpcore": "Parte de httpx",
            "h11": "Parte de httpx",
            "sniffio": "Parte de httpx",
            # Utilidades de serialización múltiples
            "msgspec": "Serialización rápida, no necesaria",
            # Utilidades de testing múltiples
            "pytest-html": "Plugin de pytest no necesario",
            "pytest-metadata": "Plugin de pytest no necesario",
        }

        # PyObjC frameworks redundantes (solo mantener los esenciales)
        self.essential_pyobjc = {
            "pyobjc-core",
            "pyobjc-framework-Cocoa",
            "pyobjc-framework-Quartz",
            "pyobjc-framework-Security",
            "pyobjc-framework-WebKit",
        }

        # Dependencias a mantener (críticas para Python 3.10)
        self.critical_dependencies = {
            "Flask==3.1.1",
            "Werkzeug==3.1.3",
            "pymongo==4.10.1",
            "boto3==1.40.16",
            "pandas==2.0.3",
            "pydantic==2.11.7",
            "typing_extensions==4.14.0",
            "python-dotenv==1.0.1",
            "gunicorn==23.0.0",
            "pytest==8.2.0",
            "black==24.8.0",
            "pylint==3.3.7",
        }

    def check_python_version(self) -> bool:
        """Verificar que estamos usando Python 3.10"""
        version = sys.version_info
        if version.major == 3 and version.minor == 10:
            logger.info(
                f"✅ Python {version.major}.{version.minor}.{version.micro} detectado"
            )
            return True
        else:
            logger.error(
                f"❌ Se requiere Python 3.10, detectado: {version.major}.{version.minor}.{version.micro}"
            )
            return False

    def get_installed_packages(self) -> Dict[str, str]:
        """Obtener lista de paquetes instalados"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
            )
            packages = {}
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==", 1)
                    packages[name.lower()] = version
            logger.info(f"📦 {len(packages)} paquetes instalados detectados")
            return packages
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error obteniendo paquetes instalados: {e}")
            return {}

    def identify_redundant_packages(
        self, installed_packages: Dict[str, str]
    ) -> List[str]:
        """Identificar paquetes redundantes"""
        redundant = []

        # Verificar paquetes redundantes conocidos
        for package in self.redundant_packages:
            if package.lower() in installed_packages:
                redundant.append(package)
                logger.info(
                    f"🔍 Paquete redundante detectado: {package} - {self.redundant_packages[package]}"
                )

        # Verificar PyObjC frameworks redundantes
        pyobjc_packages = [
            pkg for pkg in installed_packages if pkg.startswith("pyobjc-framework-")
        ]
        redundant_pyobjc = [
            pkg for pkg in pyobjc_packages if pkg not in self.essential_pyobjc
        ]

        if redundant_pyobjc:
            redundant.extend(redundant_pyobjc)
            logger.info(
                f"🔍 {len(redundant_pyobjc)} frameworks PyObjC redundantes detectados"
            )

        return redundant

    def create_cleanup_plan(
        self, redundant_packages: List[str]
    ) -> Dict[str, List[str]]:
        """Crear plan de limpieza"""
        plan = {
            "remove": redundant_packages,
            "keep": list(self.critical_dependencies),
            "test_after": ["Flask", "pymongo", "boto3", "pandas", "pytest"],
        }

        logger.info("📋 Plan de limpieza creado:")
        logger.info(f"   - Eliminar: {len(plan['remove'])} paquetes")
        logger.info(f"   - Mantener: {len(plan['keep'])} dependencias críticas")
        logger.info(f"   - Probar: {len(plan['test_after'])} funcionalidades")

        return plan

    def backup_current_state(self) -> str:
        """Crear backup del estado actual"""
        timestamp = subprocess.run(
            ["date", "+%Y%m%d_%H%M%S"], capture_output=True, text=True, check=True
        ).stdout.strip()

        backup_file = self.backup_dir / f"pre_cleanup_state_{timestamp}.json"

        # Obtener estado actual
        installed = self.get_installed_packages()

        backup_data = {
            "timestamp": timestamp,
            "python_version": (
                f"{sys.version_info.major}.{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
            "installed_packages": installed,
            "redundant_packages": list(self.redundant_packages.keys()),
            "essential_pyobjc": list(self.essential_pyobjc),
            "critical_dependencies": list(self.critical_dependencies),
        }

        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"💾 Backup creado: {backup_file}")
        return str(backup_file)

    def remove_packages(self, packages: List[str]) -> bool:
        """Eliminar paquetes redundantes"""
        if not packages:
            logger.info("✅ No hay paquetes para eliminar")
            return True

        logger.info(f"🗑️  Eliminando {len(packages)} paquetes redundantes...")

        for package in packages:
            try:
                logger.info(f"   - Eliminando {package}...")
                subprocess.run(  # pyright: ignore[reportUnusedCallResult]
                    [sys.executable, "-m", "pip", "uninstall", "-y", package],
                    check=True,
                    capture_output=True,
                )
                logger.info(f"   ✅ {package} eliminado")
            except subprocess.CalledProcessError as e:
                logger.warning(f"   ⚠️  No se pudo eliminar {package}: {e}")
                continue

        return True

    def test_critical_functionality(self, test_packages: List[str]) -> bool:
        """Probar funcionalidades críticas después de la limpieza"""
        logger.info("🧪 Probando funcionalidades críticas...")

        test_results = {}

        for package in test_packages:
            try:
                # Intentar importar el paquete
                subprocess.run(  # pyright: ignore[reportUnusedCallResult]
                    [
                        sys.executable,
                        "-c",
                        f'import {package}; print(f"✅ {package} funciona correctamente")',
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                test_results[package] = True
                logger.info(f"   ✅ {package}: OK")
            except subprocess.CalledProcessError as e:
                test_results[package] = False
                logger.error(f"   ❌ {package}: ERROR - {e}")

        success_count = sum(test_results.values())
        total_count = len(test_results)

        logger.info(f"📊 Resultados de pruebas: {success_count}/{total_count} exitosas")

        return success_count == total_count

    def generate_clean_requirements(self) -> str:
        """Generar archivo requirements.txt limpio"""
        timestamp = subprocess.run(
            ["date", "+%Y%m%d_%H%M%S"], capture_output=True, text=True, check=True
        ).stdout.strip()

        clean_requirements = (
            self.project_root / f"requirements_clean_py310_{timestamp}.txt"
        )

        # Obtener paquetes instalados después de la limpieza
        installed = self.get_installed_packages()

        # Filtrar solo los paquetes necesarios
        essential_packages = []
        for package, version in installed.items():
            # Incluir dependencias críticas
            if any(
                crit_pkg.split("==")[0].lower() == package
                for crit_pkg in self.critical_dependencies
            ):
                essential_packages.append(f"{package}=={version}")
            # Incluir dependencias de Flask
            elif package in [
                "jinja2",
                "click",
                "blinker",
                "itsdangerous",
                "markupsafe",
            ]:
                essential_packages.append(f"{package}=={version}")
            # Incluir dependencias de MongoDB
            elif package in ["dnspython"]:
                essential_packages.append(f"{package}=={version}")
            # Incluir dependencias de AWS
            elif package in ["botocore", "s3transfer", "jmespath", "python-dateutil"]:
                essential_packages.append(f"{package}=={version}")

        # Ordenar alfabéticamente
        essential_packages.sort()

        with open(clean_requirements, "w") as f:
            f.write(
                "# Requirements limpios para Python 3.10\n"
            )  # pyright: ignore[reportUnusedCallResult]
            f.write(
                "# Generado automáticamente por cleanup_dependencies_py310.py\n"
            )  # pyright: ignore[reportUnusedCallResult]
            f.write(
                f"# Fecha: {timestamp}\n\n"
            )  # pyright: ignore[reportUnusedCallResult]
            for package in essential_packages:
                f.write(f"{package}\n")  # pyright: ignore[reportUnusedCallResult]

        logger.info(f"📝 Archivo requirements limpio generado: {clean_requirements}")
        return str(clean_requirements)

    def run_cleanup(self) -> bool:
        """Ejecutar proceso completo de limpieza"""
        logger.info("🚀 Iniciando limpieza de dependencias para Python 3.10")

        # Verificar versión de Python
        if not self.check_python_version():
            return False

        # Crear backup del estado actual
        backup_file = self.backup_current_state()

        # Obtener paquetes instalados
        installed_packages = self.get_installed_packages()
        if not installed_packages:
            logger.error("❌ No se pudieron obtener los paquetes instalados")
            return False

        # Identificar paquetes redundantes
        redundant_packages = self.identify_redundant_packages(installed_packages)

        if not redundant_packages:
            logger.info("✅ No se encontraron paquetes redundantes")
            return True

        # Crear plan de limpieza
        plan = self.create_cleanup_plan(redundant_packages)

        # Confirmar con el usuario
        print("\n📋 Plan de limpieza:")
        print(f"   - Paquetes a eliminar: {len(plan['remove'])}")
        print(f"   - Dependencias críticas a mantener: {len(plan['keep'])}")
        print(f"   - Backup creado en: {backup_file}")

        response = input("\n¿Continuar con la limpieza? (y/N): ").strip().lower()
        if response != "y":
            logger.info("❌ Limpieza cancelada por el usuario")
            return False

        # Eliminar paquetes redundantes
        if not self.remove_packages(plan["remove"]):
            logger.error("❌ Error durante la eliminación de paquetes")
            return False

        # Probar funcionalidades críticas
        if not self.test_critical_functionality(plan["test_after"]):
            logger.warning("⚠️  Algunas funcionalidades críticas fallaron")
            logger.info("💡 Revisa el log para más detalles")

        # Generar requirements limpio
        clean_requirements = self.generate_clean_requirements()

        logger.info("✅ Limpieza de dependencias completada")
        logger.info(f"📁 Archivo requirements limpio: {clean_requirements}")
        logger.info(f"📁 Backup del estado anterior: {backup_file}")

        return True


def main():
    """Función principal"""
    try:
        cleaner = DependencyCleaner()
        success = cleaner.run_cleanup()

        if success:
            print("\n🎉 Limpieza completada exitosamente!")
            print("📋 Revisa los archivos generados:")
            print("   - requirements_clean_py310_*.txt")
            print("   - logs/dependency_cleanup.log")
            print("   - backups/pre_cleanup_state_*.json")
        else:
            print("\n❌ La limpieza falló. Revisa los logs para más detalles.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Limpieza interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
