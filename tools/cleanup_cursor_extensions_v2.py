#!/usr/bin/env python3
"""
Script de limpieza de extensiones de Cursor IDE - Versión 2.0
Elimina extensiones incompatibles, duplicadas y problemáticas identificadas

Autor: Sistema de limpieza automática
Fecha: 2025-08-27
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cursor_extensions_cleanup_v2.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class CursorExtensionsCleanerV2:
    """Clase para limpiar extensiones de Cursor IDE - Versión mejorada"""

    def __init__(self) -> None:
        super().__init__()
        self.cursor_extensions_dir = Path.home() / ".cursor" / "extensions"
        self.backup_dir = Path.cwd() / "backups" / "cursor_extensions"
        self.logs_dir = Path.cwd() / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Extensiones problemáticas identificadas (versión mejorada)
        self.problematic_extensions = {
            # === LINTERS Y FORMATEADORES DUPLICADOS ===
            "charliermarsh.ruff-2025.24.0-darwin-arm64": "Linter Python - Mantener solo uno",
            "ms-python.flake8-2024.0.0-universal": "Linter Python - Conflicto con Ruff",
            "ms-python.black-formatter-2024.6.0-universal": "Formateador - Mantener solo uno",
            "magicstack.magicpython-1.1.1-universal": "Linter Python - Redundante",
            # === TYPE CHECKERS DUPLICADOS ===
            "anysphere.cursorpyright-1.0.9": "Type checker - Mantener solo uno",
            "ms-python.mypy-type-checker-2025.2.0-universal": "Type checker - Conflicto con Pyright",
            # === INTELLISENSE DUPLICADO ===
            "ms-python.python-2025.6.1-darwin-arm64": "IntelliSense - Conflicto con Cursor",
            # === DEBUGGERS DUPLICADOS ===
            "ms-python.debugpy-2025.11.2025061301-darwin-arm64": "Debugger - Mantener solo uno",
            # === TESTING DUPLICADO ===
            "littlefoxteam.vscode-python-test-adapter-0.8.2": "Testing - Redundante",
            # === GIT TOOLS DUPLICADOS ===
            "eamodio.gitlens-17.4.0-universal": "Git - Versión duplicada",
            "eamodio.gitlens-17.4.1-universal": "Git - Mantener solo la más reciente",
            # === PYTHON EXTENSIONS REDUNDANTES ===
            "donjayamanne.python-environment-manager-1.2.7": "Python env manager - Redundante",
            "donjayamanne.python-extension-pack-1.7.0": "Python extension pack - Redundante",
            "ericsia.pythonsnippets3-3.3.20": "Python snippets - Redundante",
            "kevinrose.vsc-python-indent-1.21.0": "Python indent - Redundante",
            "mgesbert.python-path-0.0.14": "Python path - Redundante",
            "ms-python.isort-2025.0.0": "Python isort - Redundante con Black",
            "tushortz.python-extended-snippets-0.0.1": "Python snippets - Redundante",
            # === TEMAS DUPLICADOS (mantener solo 2) ===
            "arcticicestudio.nord-visual-studio-code-0.19.0": "Tema - Demasiados temas instalados",
            "dracula-theme.theme-dracula-2.25.1": "Tema - Demasiados temas instalados",
            "github.github-vscode-theme-6.3.5": "Tema - Demasiados temas instalados",
            "teabyii.ayu-1.0.5": "Tema - Demasiados temas instalados",
            "robbowen.synthwave-vscode-0.1.20": "Tema - Demasiados temas instalados",
            "ahmadawais.shades-of-purple-7.3.2": "Tema - Demasiados temas instalados",
            "eliverlara.andromeda-1.8.2": "Tema - Demasiados temas instalados",
            "gerane.theme-flatlandmonokai-0.0.6": "Tema - Demasiados temas instalados",
            "sdras.night-owl-2.1.1": "Tema - Demasiados temas instalados",
            "azemoh.one-monokai-0.5.2": "Tema - Demasiados temas instalados",
            "wholroyd.jinja-0.0.8": "Tema - Demasiados temas instalados",
            "whizkydee.material-palenight-theme-2.0.4": "Tema - Demasiados temas instalados",
            "fabiospampinato.vscode-monokai-night-1.7.1": "Tema - Demasiados temas instalados",
            "zhuangtongfa.material-theme-3.19.0": "Tema - Demasiados temas instalados",
            "enkia.tokyo-night-1.1.2": "Tema - Demasiados temas instalados",
            # === ICONOS DUPLICADOS ===
            "vscode-icons-team.vscode-icons-12.14.0-universal": "Iconos - Demasiados paquetes de iconos",
            "miguelsolorio.fluent-icons-0.0.19": "Iconos - Demasiados paquetes de iconos",
            "wayou.vscode-icons-mac-7.25.3": "Iconos - Demasiados paquetes de iconos",
            "pkief.material-icon-theme-5.26.0-universal": "Iconos - Demasiados paquetes de iconos",
            "miguelsolorio.symbols-0.0.24": "Iconos - Demasiados paquetes de iconos",
            # === AI ASSISTANTS DUPLICADOS ===
            "amazonwebservices.amazon-q-vscode-1.91.0-universal": "AI Assistant - Demasiados asistentes IA",
            "google.geminicodeassist-2.46.0-universal": "AI Assistant - Demasiados asistentes IA",
            "saoudrizwan.claude-dev-3.26.5-universal": "AI Assistant - Demasiados asistentes IA",
            "danielsanmedium.dscodegpt-3.13.1-universal": "AI Assistant - Demasiados asistentes IA",
            "genieai.chatgpt-vscode-0.0.13": "AI Assistant - Demasiados asistentes IA",
            "openai.openai-chatgpt-adhoc-0.0.1731981761": "AI Assistant - Demasiados asistentes IA",
            "bito.bito-1.5.9-universal": "AI Assistant - Demasiados asistentes IA",
            "codium.codium-1.6.26-universal": "AI Assistant - Demasiados asistentes IA",
            # === SPELL CHECKERS DUPLICADOS ===
            "ban.spellright-3.0.144": "Spell Checker - Demasiados correctores ortográficos",
            "streetsidesoftware.code-spell-checker-spanish-2.3.8-universal": "Spell Checker - Demasiados correctores ortográficos",
            # === EXTENSIONES REDUNDANTES ADICIONALES ===
            "donjayamanne.githistory-0.6.20": "Git History - Redundante con GitLens",
            "mhutchie.git-graph-1.30.0": "Git Graph - Redundante con GitLens",
            "waderyan.gitblame-11.1.4-universal": "Git Blame - Redundante con GitLens",
            "felipecaputo.git-project-manager-1.8.2": "Git Project Manager - Redundante",
            "alefragnani.project-manager-12.8.0": "Project Manager - Redundante",
            # === EXTENSIONES DE DESARROLLO REDUNDANTES ===
            "formulahendry.code-runner-0.12.2": "Code Runner - Redundante",
            "glenn2223.live-sass-6.1.2": "Live Sass - Redundante",
            "ritwickdey.liveserver-5.7.9": "Live Server - Redundante",
            "ms-vscode.live-server-0.4.15": "Live Server - Redundante",
            # === EXTENSIONES DE UTILIDAD REDUNDANTES ===
            "shardulm94.trailing-spaces-0.4.1": "Trailing Spaces - Redundante",
            "oderwat.indent-rainbow-8.3.1": "Indent Rainbow - Redundante",
            "albert.tabout-0.2.2": "Tab Out - Redundante",
            "dzhavat.bracket-pair-toggler-0.0.3": "Bracket Pair Toggler - Redundante",
        }

        # Extensiones a mantener (esenciales)
        self.essential_extensions = {
            "anysphere.cursorpyright",  # Type checker principal
            "charliermarsh.ruff",  # Linter principal
            "ms-python.black-formatter",  # Formateador principal
            "ms-python.debugpy",  # Debugger principal
            "ms-python.pytest-adapter",  # Testing principal
            "eamodio.gitlens",  # Git principal
            "github.copilot",  # AI Assistant principal
            "ms-vscode.vscode-json",  # JSON support
            "ms-vscode.vscode-markdown",  # Markdown support
            "ms-vscode.vscode-yaml",  # YAML support
            "ms-vscode.vscode-xml",  # XML support
            "ms-vscode.vscode-css",  # CSS support
            "ms-vscode.vscode-html",  # HTML support
            "ms-vscode.vscode-javascript",  # JavaScript support
            "ms-vscode.vscode-typescript",  # TypeScript support
            "ms-vscode.vscode-python",  # Python support básico
            "ms-vscode.vscode-git",  # Git básico
            "ms-vscode.vscode-terminal",  # Terminal
            "ms-vscode.vscode-explorer",  # Explorer
            "ms-vscode.vscode-settings",  # Settings
            "ms-vscode.vscode-snippets",  # Snippets
            "ms-vscode.vscode-extension-api",  # Extension API
            "ms-vscode.vscode-extension-test-adapter",  # Extension testing
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
        backup_file = self.backup_dir / f"cursor_extensions_backup_v2_{timestamp}.json"

        # Obtener estado actual
        installed = self.get_installed_extensions()
        problematic = self.identify_problematic_extensions(installed)

        backup_data = {
            "timestamp": timestamp,
            "version": "2.0",
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
            self.logs_dir / f"cursor_extensions_cleanup_v2_report_{timestamp}.json"
        )

        # Obtener extensiones restantes
        remaining_extensions = self.get_installed_extensions()

        report_data = {
            "timestamp": timestamp,
            "version": "2.0",
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
                "reduction_percentage": round(
                    (
                        len(removed_extensions)
                        / (len(remaining_extensions) + len(removed_extensions))
                    )
                    * 100,
                    1,
                ),
            },
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 Reporte de limpieza generado: {report_file}")
        return str(report_file)

    def run_cleanup(self) -> bool:
        """Ejecutar proceso completo de limpieza"""
        logger.info("🚀 Iniciando limpieza de extensiones de Cursor IDE - Versión 2.0")

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
        print("\n📋 Plan de limpieza de extensiones Cursor - Versión 2.0:")
        print(f"   - Extensiones a eliminar: {len(plan['remove'])}")
        print(f"   - Extensiones esenciales a mantener: {len(plan['keep'])}")
        print(f"   - Backup creado en: {backup_file}")
        print(
            f"   - Reducción estimada: {round((len(plan['remove']) / len(installed_extensions)) * 100, 1)}%"
        )

        print("\n🔍 Categorías de extensiones problemáticas:")
        categories: Dict[str, List[str]] = {}
        for ext in plan["remove"]:
            reason = self.problematic_extensions[ext]
            category = reason.split(" - ")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(ext)

        for category, exts in categories.items():
            print(f"   - {category}: {len(exts)} extensiones")

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
        cleaner = CursorExtensionsCleanerV2()
        success = cleaner.run_cleanup()

        if success:
            print("\n🎉 Limpieza de extensiones completada exitosamente!")
            print("📋 Revisa los archivos generados:")
            print("   - backups/cursor_extensions/")
            print("   - logs/cursor_extensions_cleanup_v2_report_*.json")
            print("   - logs/cursor_extensions_cleanup_v2.log")
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
