#!/usr/bin/env python3
"""
Script para configurar el corrector ortográfico en el IDE
Crea configuraciones para VS Code, PyCharm y otros IDEs
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List


class IDESpellCheckSetup:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.vscode_dir = self.project_root / ".vscode"
        self.vscode_dir.mkdir(exist_ok=True)

    def setup_vscode(self) -> None:
        """Configurar VS Code para el corrector ortográfico"""
        print("🔧 Configurando VS Code...")

        # Configuración principal de VS Code
        vscode_settings = {
            "spellright.language": ["es", "en"],
            "spellright.documentTypes": [
                "markdown",
                "latex",
                "plaintext",
                "html",
                "css",
            ],
            "spellright.parserByClass": {
                "markdown": "markdown",
                "latex": "latex",
                "plaintext": "plaintext",
                "html": "html",
                "css": "css",
            },
            "spellright.ignoreFiles": [
                "**/node_modules/**",
                "**/.git/**",
                "**/.venv/**",
                "**/__pycache__/**",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.pyd",
                "**/.pytest_cache/**",
                "**/dist/**",
                "**/build/**",
                "**/*.spec",
                "**/pyproject.toml.backup*",
            ],
            "spellright.ignoreRegExpsByClass": {
                "markdown": [
                    "/\\b[A-Z]{2,}\\b/g",
                    "/\\b\\d+\\b/g",
                    "/`[^`]+`/g",
                    "/\\$[^$]+\\$/g",
                    "/\\[([^\\]]+)\\]\\([^)]+\\)/g",
                ],
                "plaintext": [
                    "/\\b[A-Z]{2,}\\b/g",
                    "/\\b\\d+\\b/g",
                    "/`[^`]+`/g",
                    "/\\$[^$]+\\$/g",
                ],
                "html": ["/<[^>]+>/g", "/\\b[A-Z]{2,}\\b/g", "/\\b\\d+\\b/g"],
                "css": ["/\\b[A-Z]{2,}\\b/g", "/\\b\\d+\\b/g", "/#[0-9a-fA-F]{3,6}/g"],
            },
            "spellright.ignoreWords": [
                # Palabras específicas del proyecto
                "edefrutos",
                "catalogotablas",
                "catalogo",
                "tablas",
                "edf",
                "edefrutos2025",
                "xyz",
                "httpdocs",
                "vhosts",
                # Términos técnicos
                "api",
                "http",
                "ssl",
                "tls",
                "json",
                "xml",
                "sql",
                "mongodb",
                "redis",
                "aws",
                "s3",
                "gcp",
                "oauth",
                "jwt",
                "csrf",
                "cors",
                # Módulos de Python
                "flask",
                "pymongo",
                "werkzeug",
                "jinja2",
                "boto3",
                "requests",
                "numpy",
                "pandas",
                "matplotlib",
                "pytest",
                "black",
                "flake8",
                "gunicorn",
                "dotenv",
                "bcrypt",
                "cryptography",
                "pillow",
                # Extensiones y versiones
                "pyc",
                "pyo",
                "pyd",
                "venv",
                "pytest",
                "mypy",
                "ruff",
                # Palabras en español comunes
                "ón",
                "intérprete",
                "mantenimiento",
                "utilidades",
                "unitarias",
                "formateo",
                "linting",
                "configuración",
                "aplicación",
                "autenticación",
                "autorización",
                "validación",
                "verificación",
            ],
            "spellright.words": [
                # Palabras personalizadas del proyecto
                "edefrutos",
                "catalogotablas",
                "edf",
                "xyz",
            ],
            "files.associations": {
                "*.toml": "toml",
                "*.yaml": "yaml",
                "*.yml": "yaml",
                "*.json": "json",
                "*.md": "markdown",
                "*.py": "python",
                "*.js": "javascript",
                "*.html": "html",
                "*.css": "css",
            },
            "python.defaultInterpreterPath": "./.venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.organizeImports": True},
        }

        # Guardar configuración de VS Code
        settings_file = self.vscode_dir / "settings.json"
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(vscode_settings, f, indent=2, ensure_ascii=False)

        print(f"✅ Configuración de VS Code guardada: {settings_file}")

    def setup_pycharm(self) -> None:
        """Configurar PyCharm para el corrector ortográfico"""
        print("🔧 Configurando PyCharm...")

        # Crear archivo de configuración para PyCharm
        pycharm_config = {
            "spell_checker": {
                "enabled": True,
                "languages": ["en", "es"],
                "ignore_words": [
                    "edefrutos",
                    "catalogotablas",
                    "edf",
                    "xyz",
                    "api",
                    "http",
                    "ssl",
                    "tls",
                    "json",
                    "xml",
                    "sql",
                    "flask",
                    "pymongo",
                    "werkzeug",
                    "jinja2",
                    "boto3",
                ],
                "ignore_patterns": [
                    "**/venv/**",
                    "**/__pycache__/**",
                    "**/*.pyc",
                    "**/node_modules/**",
                    "**/.git/**",
                ],
            },
            "file_types": {
                "python": {
                    "check_spelling": False,
                    "check_comments": True,
                    "check_strings": False,
                },
                "markdown": {
                    "check_spelling": True,
                    "check_comments": True,
                    "check_strings": True,
                },
                "html": {
                    "check_spelling": True,
                    "check_comments": True,
                    "check_strings": True,
                },
                "css": {
                    "check_spelling": False,
                    "check_comments": True,
                    "check_strings": False,
                },
            },
        }

        # Guardar configuración de PyCharm
        pycharm_file = self.project_root / "pycharm_spell_check_config.json"
        with open(pycharm_file, "w", encoding="utf-8") as f:
            json.dump(pycharm_config, f, indent=2, ensure_ascii=False)

        print(f"✅ Configuración de PyCharm guardada: {pycharm_file}")

    def setup_cspell_config(self) -> None:
        """Configurar cspell (Code Spell Checker)"""
        print("🔧 Configurando cspell...")

        cspell_config = {
            "version": "0.2",
            "language": "en,es",
            "words": [
                "edefrutos",
                "catalogotablas",
                "edf",
                "xyz",
                "httpdocs",
                "vhosts",
                "api",
                "http",
                "ssl",
                "tls",
                "json",
                "xml",
                "sql",
                "mongodb",
                "redis",
                "aws",
                "s3",
                "gcp",
                "oauth",
                "jwt",
                "csrf",
                "cors",
                "flask",
                "pymongo",
                "werkzeug",
                "jinja2",
                "boto3",
                "requests",
                "numpy",
                "pandas",
                "matplotlib",
                "pytest",
                "black",
                "flake8",
                "gunicorn",
                "dotenv",
                "bcrypt",
                "cryptography",
                "pillow",
            ],
            "ignoreWords": ["pyc", "pyo", "pyd", "venv", "pytest", "mypy", "ruff"],
            "ignorePaths": [
                "node_modules/**",
                ".git/**",
                "venv/**",
                "__pycache__/**",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                "build/**",
                "dist/**",
                "*.egg-info/**",
                "*.spec",
                "pyproject.toml.backup*",
            ],
            "allowCompoundWords": True,
            "dictionaries": ["en_US", "es_ES", "technical-terms"],
            "dictionaryDefinitions": [
                {
                    "name": "technical-terms",
                    "path": "./config/dictionaries/technical_terms.txt",
                    "addWords": True,
                },
                {
                    "name": "spanish-words",
                    "path": "./config/dictionaries/spanish_words.txt",
                    "addWords": True,
                },
                {
                    "name": "english-words",
                    "path": "./config/dictionaries/english_words.txt",
                    "addWords": True,
                },
            ],
        }

        # Guardar configuración de cspell
        cspell_file = self.project_root / "cspell.json"
        with open(cspell_file, "w", encoding="utf-8") as f:
            json.dump(cspell_config, f, indent=2, ensure_ascii=False)

        print(f"✅ Configuración de cspell guardada: {cspell_file}")

    def create_install_instructions(self) -> None:
        """Crear instrucciones de instalación"""
        print("📝 Creando instrucciones de instalación...")

        instructions = """# Configuración del Correcto Ortográfico

## VS Code

1. Instalar extensiones:
   - Code Spell Checker (cspell)
   - Spell Right

2. La configuración ya está creada en `.vscode/settings.json`

## PyCharm

1. Ir a Settings > Editor > Natural Languages > Spelling
2. Configurar según `pycharm_spell_check_config.json`

## cspell (Code Spell Checker)

1. Instalar globalmente:
   ```bash
   npm install -g cspell
   ```

2. La configuración ya está creada en `cspell.json`

3. Ejecutar verificación:
   ```bash
   cspell "**/*.{py,md,html,js,css,txt}"
   ```

## Archivos de configuración creados:

- `.vscode/settings.json` - Configuración de VS Code
- `cspell.json` - Configuración de cspell
- `pycharm_spell_check_config.json` - Configuración de PyCharm
- `config/dictionaries/` - Diccionarios temáticos

## Comandos útiles:

```bash
# Verificar ortografía con cspell
cspell "**/*.{py,md,html,js,css,txt}"

# Ejecutar flujo completo de gestión
python tools/complete_spell_check_workflow.py

# Verificar archivo específico
python tools/quick_spell_check.py archivo.txt
```

## Notas importantes:

- Los archivos de código (.py, .js) tienen verificación de ortografía deshabilitada
- Los archivos de documentación (.md, .txt) tienen verificación habilitada
- Los términos técnicos y palabras del proyecto están en la lista blanca
- Se ignoran automáticamente directorios como venv, __pycache__, etc.
"""

        instructions_file = self.project_root / "SPELL_CHECK_SETUP.md"
        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write(instructions)

        print(f"✅ Instrucciones guardadas: {instructions_file}")

    def run_complete_setup(self) -> None:
        """Ejecutar configuración completa"""
        print("🚀 Configurando corrector ortográfico para IDEs...")
        print("=" * 60)

        # Configurar VS Code
        self.setup_vscode()

        # Configurar PyCharm
        self.setup_pycharm()

        # Configurar cspell
        self.setup_cspell_config()

        # Crear instrucciones
        self.create_install_instructions()

        print("\n✅ Configuración completada!")
        print("\n📋 Archivos creados:")
        print(f"  📄 VS Code: .vscode/settings.json")
        print(f"  📄 cspell: cspell.json")
        print(f"  📄 PyCharm: pycharm_spell_check_config.json")
        print(f"  📄 Instrucciones: SPELL_CHECK_SETUP.md")
        print("\n📋 Próximos pasos:")
        print("  1. Instalar extensiones de VS Code (Code Spell Checker)")
        print("  2. Configurar PyCharm según las instrucciones")
        print("  3. Instalar cspell globalmente: npm install -g cspell")
        print("  4. Ejecutar: python tools/complete_spell_check_workflow.py")


def main():
    """Función principal"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."

    setup = IDESpellCheckSetup(project_root)
    setup.run_complete_setup()


if __name__ == "__main__":
    main()
