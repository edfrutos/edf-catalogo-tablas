#!/usr/bin/env python3
"""
Script de limpieza de extensiones de Cursor IDE
Elimina extensiones incompatibles y duplicadas

Autor: Sistema de limpieza automática
Fecha: 2025-08-27
"""

import os  # pyright: ignore[reportUnusedImport]
import sys
import json
import shutil
import subprocess  # pyright: ignore[reportUnusedImport]
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set  # pyright: ignore[reportUnusedImport]
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cursor_extensions_cleanup.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class CursorExtensionsCleaner:
    """Clase para limpiar extensiones de Cursor IDE"""

    def __init__(self):  # pyright: ignore[reportMissingSuperCall]
        self.cursor_extensions_dir = Path.home() / ".cursor" / "extensions"
        self.backup_dir = Path.cwd() / "backups" / "cursor_extensions"
        self.logs_dir = Path.cwd() / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Extensiones problemáticas identificadas (nombres reales)
        self.problematic_extensions = {
            # Linters y formateadores duplicados
            "charliermarsh.ruff-2025.24.0-darwin-arm64": "Linter Python - Mantener solo uno",
            "ms-python.flake8-2024.0.0-universal": "Linter Python - Conflicto con Ruff",
            "ms-python.black-formatter-2024.6.0-universal": "Formateador - Mantener solo uno",
            "magicstack.magicpython-1.1.1-universal": "Linter Python - Redundante",
            # Type checkers duplicados
            "anysphere.cursorpyright-1.0.9": "Type checker - Mantener solo uno",
            "ms-python.mypy-type-checker-2025.2.0-universal": "Type checker - Conflicto con Pyright",
            # IntelliSense duplicado
            "ms-python.python-2025.6.1-darwin-arm64": "IntelliSense - Conflicto con Cursor",
            # Debuggers duplicados
            "ms-python.debugpy-2025.11.2025061301-darwin-arm64": "Debugger - Mantener solo uno",
            # Extensiones de testing duplicadas
            "littlefoxteam.vscode-python-test-adapter-0.8.2": "Testing - Redundante",
            # Extensiones de Git duplicadas
            "eamodio.gitlens-17.4.0-universal": "Git - Versión duplicada",
            "eamodio.gitlens-17.4.1-universal": "Git - Mantener solo la más reciente",
            # Extensiones de Python redundantes
            "donjayamanne.python-environment-manager-1.2.7": "Python env manager - Redundante",
            "donjayamanne.python-extension-pack-1.7.0": "Python extension pack - Redundante",
            "ericsia.pythonsnippets3-3.3.20": "Python snippets - Redundante",
            "kevinrose.vsc-python-indent-1.21.0": "Python indent - Redundante",
            "mgesbert.python-path-0.0.14": "Python path - Redundante",
            "ms-python.isort-2025.0.0": "Python isort - Redundante con Black",
            "tushortz.python-extended-snippets-0.0.1": "Python snippets - Redundante",
        }

        # Extensiones a mantener (esenciales)
        self.essential_extensions = {
            "anysphere.cursorpyright",  # Type checker principal
            "charliermarsh.ruff",  # Linter principal
            "ms-python.black-formatter",  # Formateador principal
            "ms-python.debugpy",  # Debugger principal
            "ms-python.pytest-adapter",  # Testing principal
            "eamodio.gitlens",  # Git principal
            "ms-vscode.vscode-json",  # JSON support
            "ms-vscode.vscode-markdown",  # Markdown support
            "ms-vscode.vscode-yaml",  # YAML support
            "ms-vscode.vscode-xml",  # XML support
            "ms-vscode.vscode-css",  # CSS support
            "ms-vscode.vscode-html",  # HTML support
            "ms-vscode.vscode-javascript",  # JavaScript support
            "ms-vscode.vscode-typescript",  # TypeScript support
        }

    def get_installed_extensions(self) -> List[str]:
        """Obtener lista de extensiones instaladas"""
        try:
            extensions = []
            for item in self.cursor_extensions_dir.iterdir():
                if item.is_dir():
                    extensions.append(item.name)
            logger.info(f"📦 {len(extensions)} extensiones instaladas detectadas")
            return extensions
        except Exception as e:
            logger.error(f"❌ Error obteniendo extensiones: {e}")
            return []

    def identify_problematic_extensions(
        self, installed_extensions: List[str]
    ) -> List[str]:
        """Identificar extensiones problemáticas"""
        problematic = []

        for extension in installed_extensions:
            if extension in self.problematic_extensions:
                problematic.append(extension)
                logger.info(
                    f"🔍 Extensión problemática detectada: {extension} - {self.problematic_extensions[extension]}"
                )

        return problematic

    def create_cleanup_plan(
        self, problematic_extensions: List[str]
    ) -> Dict[str, List[str]]:
        """Crear plan de limpieza"""
        plan = {
            "remove": problematic_extensions,
            "keep": list(self.essential_extensions),
            "test_after": [
                "anysphere.cursorpyright",
                "charliermarsh.ruff",
                "ms-python.black-formatter",
            ],
        }

        logger.info("📋 Plan de limpieza creado:")
        logger.info(f"   - Eliminar: {len(plan['remove'])} extensiones")
        logger.info(f"   - Mantener: {len(plan['keep'])} extensiones esenciales")
        logger.info(f"   - Probar: {len(plan['test_after'])} funcionalidades")

        return plan

    def backup_current_state(self) -> str:
        """Crear backup del estado actual"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"cursor_extensions_backup_{timestamp}.json"

        # Obtener estado actual
        installed = self.get_installed_extensions()
        problematic = self.identify_problematic_extensions(installed)

        backup_data = {
            "timestamp": timestamp,
            "installed_extensions": installed,
            "problematic_extensions": problematic,
            "essential_extensions": list(self.essential_extensions),
            "total_count": len(installed),
            "problematic_count": len(problematic),
        }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Backup creado: {backup_file}")
        return str(backup_file)

    def remove_extension(self, extension_name: str) -> bool:
        """Eliminar una extensión específica"""
        try:
            extension_path = self.cursor_extensions_dir / extension_name
            if extension_path.exists():
                shutil.rmtree(extension_path)
                logger.info(f"   ✅ {extension_name} eliminada")
                return True
            else:
                logger.warning(f"   ⚠️  {extension_name} no encontrada")
                return False
        except Exception as e:
            logger.error(f"   ❌ Error eliminando {extension_name}: {e}")
            return False

    def remove_extensions(self, extensions: List[str]) -> Dict[str, bool]:
        """Eliminar extensiones problemáticas"""
        if not extensions:
            logger.info("✅ No hay extensiones para eliminar")
            return {}

        logger.info(f"🗑️  Eliminando {len(extensions)} extensiones problemáticas...")

        results = {}
        for extension in extensions:
            results[extension] = self.remove_extension(extension)

        return results

    def test_essential_functionality(self, test_extensions: List[str]) -> bool:
        """Probar funcionalidades esenciales después de la limpieza"""
        logger.info("🧪 Probando funcionalidades esenciales...")

        test_results = {}
        for extension in test_extensions:
            extension_path = self.cursor_extensions_dir / extension
            if extension_path.exists():
                test_results[extension] = True
                logger.info(f"   ✅ {extension}: OK")
            else:
                test_results[extension] = False
                logger.error(f"   ❌ {extension}: NO ENCONTRADA")

        success_count = sum(test_results.values())
        total_count = len(test_results)

        logger.info(f"📊 Resultados de pruebas: {success_count}/{total_count} exitosas")
        return success_count == total_count

    def generate_cleanup_report(
        self, removed_extensions: Dict[str, bool], backup_file: str
    ) -> str:
        """Generar reporte de limpieza"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = (
            self.logs_dir / f"cursor_extensions_cleanup_report_{timestamp}.json"
        )

        # Obtener extensiones restantes
        remaining_extensions = self.get_installed_extensions()

        report_data = {
            "timestamp": timestamp,
            "backup_file": backup_file,
            "removed_extensions": {
                ext: {
                    "success": success,
                    "reason": self.problematic_extensions.get(ext, "No especificado"),
                }
                for ext, success in removed_extensions.items()
            },
            "remaining_extensions": remaining_extensions,
            "essential_extensions": list(self.essential_extensions),
            "summary": {
                "total_removed": len(removed_extensions),
                "successfully_removed": sum(removed_extensions.values()),
                "remaining_count": len(remaining_extensions),
                "essential_count": len(self.essential_extensions),
            },
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 Reporte de limpieza generado: {report_file}")
        return str(report_file)

    def run_cleanup(self) -> bool:
        """Ejecutar proceso completo de limpieza"""
        logger.info("🚀 Iniciando limpieza de extensiones de Cursor IDE")

        # Verificar que el directorio de extensiones existe
        if not self.cursor_extensions_dir.exists():
            logger.error(
                f"❌ Directorio de extensiones no encontrado: {self.cursor_extensions_dir}"
            )
            return False

        # Crear backup del estado actual
        backup_file = self.backup_current_state()

        # Obtener extensiones instaladas
        installed_extensions = self.get_installed_extensions()
        if not installed_extensions:
            logger.error("❌ No se pudieron obtener las extensiones instaladas")
            return False

        # Identificar extensiones problemáticas
        problematic_extensions = self.identify_problematic_extensions(
            installed_extensions
        )

        if not problematic_extensions:
            logger.info("✅ No se encontraron extensiones problemáticas")
            return True

        # Crear plan de limpieza
        plan = self.create_cleanup_plan(problematic_extensions)

        # Mostrar resumen
        print("\n📋 Plan de limpieza de extensiones Cursor:")
        print(f"   - Extensiones a eliminar: {len(plan['remove'])}")
        print(f"   - Extensiones esenciales a mantener: {len(plan['keep'])}")
        print(f"   - Backup creado en: {backup_file}")
        print("\n🔍 Extensiones problemáticas detectadas:")
        for ext in plan["remove"]:
            print(f"   - {ext}: {self.problematic_extensions[ext]}")

        # Confirmar con el usuario
        response = input("\n¿Continuar con la limpieza? (y/N): ").strip().lower()
        if response != "y":
            logger.info("❌ Limpieza cancelada por el usuario")
            return False

        # Eliminar extensiones problemáticas
        removed_results = self.remove_extensions(plan["remove"])

        # Probar funcionalidades esenciales
        if not self.test_essential_functionality(plan["test_after"]):
            logger.warning("⚠️  Algunas funcionalidades esenciales fallaron")
            logger.info("💡 Revisa el log para más detalles")

        # Generar reporte
        report_file = self.generate_cleanup_report(removed_results, backup_file)

        logger.info("✅ Limpieza de extensiones completada")
        logger.info(f"📁 Backup: {backup_file}")
        logger.info(f"📁 Reporte: {report_file}")

        return True


def main():
    """Función principal"""
    try:
        cleaner = CursorExtensionsCleaner()
        success = cleaner.run_cleanup()

        if success:
            print("\n🎉 Limpieza de extensiones completada exitosamente!")
            print("📋 Revisa los archivos generados:")
            print("   - backups/cursor_extensions/")
            print("   - logs/cursor_extensions_cleanup_report_*.json")
            print("   - logs/cursor_extensions_cleanup.log")
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
