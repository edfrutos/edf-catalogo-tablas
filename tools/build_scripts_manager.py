#!/usr/bin/env python3
"""
Gestor de Scripts de Build - EDF CatalogoDeTablas
Interfaz unificada para ejecutar scripts de build organizados por categorías
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class BuildScriptsManager:
    def __init__(self):  # type: ignore
        # Obtener el directorio base del proyecto
        script_path = Path(__file__).resolve()
        self.base_dir = script_path.parent.parent
        self.tools_dir = self.base_dir / "tools"
        self.build_dir = self.tools_dir / "build"

        # Definir categorías y scripts
        self.categories = {
            "ci-cd": {
                "description": "Scripts críticos para CI/CD (GitHub Actions)",
                "scripts": [
                    "build_macos_app.sh",
                    "verify_build_environment.sh",
                    "verify_requirements.sh",
                    "fix_pyinstaller_tools_conflict_v2.sh",
                    "fix_pyinstaller_tools_conflict_v3.sh",
                    "pre_build_cleanup.sh",
                    "ci_fix_pyinstaller.sh",
                    "fix_existing_spec.sh",
                    "create_safe_spec.sh",
                    "pre_build_final_check.sh",
                ],
            },
            "documentation": {
                "description": "Scripts referenciados en documentación",
                "scripts": [
                    "build_web_app.sh",
                    "build_native_app.sh",
                    "build_all_versions.sh",
                    "fix_pyinstaller_tools_conflict.sh",
                    "clean_build.sh",
                    "verify_build_files.sh",
                    "verify_connectivity.sh",
                    "verify_spec.sh",
                    "safe_push.sh",
                ],
            },
            "utilities": {
                "description": "Scripts de utilidades generales",
                "scripts": [
                    "fix_tools_directory_conflict.sh",
                    "fix_pyinstaller_conflict.sh",
                    "diagnose_pyinstaller_conflict.sh",
                    "verify_markdown.sh",
                ],
            },
            "configuration": {
                "description": "Scripts de configuración y verificación",
                "scripts": ["verify_pyright.sh"],
            },
            "spell-check": {
                "description": "Utilidades de verificación ortográfica y corrección",
                "scripts": [
                    "quick_spell_check.py",
                    "quick_setup_spell_check.py",
                    "complete_spell_check_workflow.py",
                    "add_common_words.py",
                    "add_categorized_words.py",
                    "fix_spell_check.py",
                    "spell_check_gui.py",
                    "launch_spell_check_gui.sh",
                ],
            },
        }

    def list_categories(self) -> None:
        """Listar todas las categorías disponibles"""
        print("📁 CATEGORÍAS DE SCRIPTS DE BUILD:")
        print("=" * 50)

        for category, info in self.categories.items():
            script_count = len(info["scripts"])
            print(f"🔧 {category.upper()}")
            print(f"   📝 {info['description']}")
            print(f"   📊 Scripts: {script_count}")
            print()

    def list_scripts(self, category: str) -> None:
        """Listar scripts de una categoría específica"""
        if category not in self.categories:
            print(f"❌ Categoría '{category}' no encontrada")
            return

        info = self.categories[category]
        print(f"📁 SCRIPTS DE LA CATEGORÍA: {category.upper()}")
        print(f"📝 {info['description']}")
        print("=" * 50)

        for i, script in enumerate(info["scripts"], 1):
            script_path = self.build_dir / category / script
            if script_path.exists():
                try:
                    original_path = script_path.resolve()
                    status = "✅" if original_path.exists() else "❌"
                    print(f"{i:2d}. {status} {script}")
                    if original_path.exists():
                        print(f"      🔗 {script_path} -> {original_path}")
                except Exception as e:
                    print(f"{i:2d}. ❌ {script} (error resolving symlink: {e})")
            else:
                print(f"{i:2d}. ❌ {script} (symlink not found)")

        print()

    def execute_script(
        self, category: str, script_name: str, args: Optional[List[str]] = None
    ) -> bool:
        """Ejecutar un script específico"""
        if category not in self.categories:
            print(f"❌ Categoría '{category}' no encontrada")
            return False

        if script_name not in self.categories[category]["scripts"]:
            print(
                f"❌ Script '{script_name}' no encontrado en la categoría '{category}'"
            )
            return False

        script_path = self.build_dir / category / script_name

        if not script_path.exists():
            print(f"❌ Script no encontrado: {script_path}")
            return False

        if not script_path.is_symlink():
            print(f"⚠️  Advertencia: {script_path} no es un enlace simbólico")

        # Verificar que el script original existe
        original_path = script_path.resolve()
        if not original_path.exists():
            print(f"❌ Script original no encontrado: {original_path}")
            return False

        print(f"🚀 Ejecutando: {script_name}")
        print(f"📁 Categoría: {category}")
        print(f"🔗 Enlace: {script_path}")
        print(f"📄 Original: {original_path}")
        print("=" * 50)

        try:
            # Construir comando
            cmd = [str(script_path)]
            if args:
                cmd.extend(args)

            # Ejecutar script
            result = subprocess.run(cmd, cwd=self.base_dir, check=False)

            print("=" * 50)
            if result.returncode == 0:
                print(f"✅ Script ejecutado exitosamente: {script_name}")
                return True
            else:
                print(f"❌ Script falló con código: {result.returncode}")
                return False

        except Exception as e:
            print(f"❌ Error ejecutando script: {e}")
            return False

    def show_help(self) -> None:
        """Mostrar ayuda"""
        help_text = """
🔧 GESTOR DE SCRIPTS DE BUILD - EDF CatalogoDeTablas

USO:
    python build_scripts_manager.py [COMANDO] [OPCIONES]

COMANDOS:
    list                    Listar todas las categorías
    list <categoría>        Listar scripts de una categoría
    run <categoría> <script> [args...]  Ejecutar un script
    help                    Mostrar esta ayuda

CATEGORÍAS:
    ci-cd                   Scripts críticos para CI/CD
    documentation           Scripts de documentación
    utilities               Scripts de utilidades
    configuration           Scripts de configuración

EJEMPLOS:
    python build_scripts_manager.py list
    python build_scripts_manager.py list ci-cd
    python build_scripts_manager.py run ci-cd build_macos_app.sh
    python build_scripts_manager.py run utilities verify_markdown.sh
    python build_scripts_manager.py run documentation clean_build.sh

NOTAS:
    - Los scripts se ejecutan desde el directorio raíz del proyecto
    - Todos los scripts son enlaces simbólicos a archivos en el directorio raíz
    - Los scripts críticos (ci-cd) no deben moverse del directorio raíz
"""
        print(help_text)

    def run(self, args: List[str]) -> int:
        """Ejecutar el gestor con argumentos"""
        if not args:
            self.show_help()
            return 1

        command = args[0].lower()

        if command == "help":
            self.show_help()
            return 0

        elif command == "list":
            if len(args) > 1:
                self.list_scripts(args[1])
            else:
                self.list_categories()
            return 0

        elif command == "run":
            if len(args) < 3:
                print("❌ Uso: run <categoría> <script> [args...]")
                return 1

            category = args[1]
            script = args[2]
            script_args = args[3:] if len(args) > 3 else []

            success = self.execute_script(category, script, script_args)
            return 0 if success else 1

        else:
            print(f"❌ Comando desconocido: {command}")
            self.show_help()
            return 1


def main():
    """Función principal"""
    manager = BuildScriptsManager()
    return manager.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
