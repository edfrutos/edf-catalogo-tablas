#!/usr/bin/env python3
"""
Script rápido para configurar spell check sin escaneo completo
Usa los datos ya procesados y solo configura lo necesario
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import toml


def create_basic_configs():
    """Crear configuraciones básicas sin escaneo completo"""
    print("🚀 Configurando sistema de spell check (modo rápido)...")

    # Crear directorio de diccionarios si no existe
    dict_dir = Path("config/dictionaries")
    dict_dir.mkdir(parents=True, exist_ok=True)

    # Configuración básica de VS Code
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    vscode_settings = {
        "spellright.language": ["es", "en"],
        "spellright.documentTypes": ["markdown", "plaintext", "html"],
        "spellright.ignoreFiles": [
            "**/node_modules/**",
            "**/.git/**",
            "**/.venv/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/build/**",
            "**/dist/**",
        ],
        "spellright.ignoreWords": [
            "edefrutos",
            "catalogotablas",
            "edf",
            "xyz",
            "api",
            "http",
            "ssl",
            "json",
            "xml",
            "sql",
            "mongodb",
            "flask",
            "pymongo",
            "werkzeug",
            "jinja2",
            "boto3",
            "pytest",
            "black",
            "flake8",
            "gunicorn",
            "ón",
            "intérprete",
            "mantenimiento",
            "utilidades",
            "pycharm",
        ],
        "spellright.words": ["edefrutos", "catalogotablas", "edf", "xyz", "pycharm"],
    }

    with open(vscode_dir / "settings.json", "w", encoding="utf-8") as f:
        json.dump(vscode_settings, f, indent=2, ensure_ascii=False)

    print("✅ Configuración de VS Code creada")

    # Configuración básica de cspell
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
            "pycharm",
        ],
        "ignoreWords": ["pyc", "pyo", "pyd", "venv", "pytest", "mypy", "ruff"],
        "ignorePaths": [
            "node_modules/**",
            ".git/**",
            "venv/**",
            "__pycache__/**",
            "*.pyc",
            "build/**",
            "dist/**",
            "*.egg-info/**",
        ],
    }

    with open("cspell.json", "w", encoding="utf-8") as f:
        json.dump(cspell_config, f, indent=2, ensure_ascii=False)

    print("✅ Configuración de cspell creada")

    # Configuración básica de PyCharm
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
                "json",
                "xml",
                "sql",
                "flask",
                "pymongo",
                "werkzeug",
                "jinja2",
                "boto3",
                "pycharm",
            ],
        }
    }

    with open("pycharm_spell_check_config.json", "w", encoding="utf-8") as f:
        json.dump(pycharm_config, f, indent=2, ensure_ascii=False)

    print("✅ Configuración de PyCharm creada")


def update_pyproject_toml():
    """Actualizar pyproject.toml con palabras básicas"""
    try:
        # Leer configuración actual
        with open("pyproject.toml", encoding="utf-8") as f:
            config = toml.load(f)

        # Obtener palabras existentes
        existing_words = set(config.get("tool", {}).get("cspell", {}).get("words", []))

        # Palabras básicas a agregar
        basic_words = [
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
            "pycharm",
        ]

        # Agregar nuevas palabras
        updated_words = list(existing_words | set(basic_words))
        updated_words.sort()

        # Actualizar configuración
        if "tool" not in config:
            config["tool"] = {}
        if "cspell" not in config["tool"]:
            config["tool"]["cspell"] = {}

        config["tool"]["cspell"]["words"] = updated_words

        # Crear backup
        backup_file = (
            f"pyproject.toml.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        _ = shutil.copy("pyproject.toml", backup_file)

        # Escribir configuración actualizada
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            _ = toml.dump(config, f)

        print(f"✅ pyproject.toml actualizado con {len(basic_words)} palabras básicas")
        print(f"📄 Backup creado: {backup_file}")
        return True

    except Exception as e:
        print(f"❌ Error actualizando pyproject.toml: {e}")
        return False


def create_instructions():
    """Crear instrucciones de uso"""
    instructions = """# Configuración Rápida del Correcto Ortográfico

## ✅ Configuración Completada

Los siguientes archivos han sido creados:
- `.vscode/settings.json` - Configuración de VS Code
- `cspell.json` - Configuración de cspell
- `pycharm_spell_check_config.json` - Configuración de PyCharm
- `pyproject.toml` - Actualizado con palabras básicas

## 🚀 Próximos Pasos

### 1. Instalar Extensiones de VS Code
```bash
# En VS Code, instalar:
# - Code Spell Checker (cspell)
# - Spell Right
```

### 2. Instalar cspell Globalmente
```bash
npm install -g cspell
```

### 3. Verificar Configuración
```bash
# Verificar ortografía con cspell
cspell "**/*.{md,txt,html}"

# Verificar archivo específico
python tools/quick_spell_check.py README.md
```

## 📋 Palabras Configuradas

Se han agregado automáticamente:
- **Términos del proyecto**: edefrutos, catalogotablas, edf, xyz
- **Términos técnicos**: api, http, ssl, json, mongodb, aws, s3
- **Módulos Python**: flask, pymongo, werkzeug, jinja2, boto3
- **Herramientas**: pytest, black, flake8, gunicorn

## 🎯 Uso

El corrector ortográfico ahora:
- ✅ Ignora archivos de código (.py, .js)
- ✅ Verifica documentación (.md, .txt, .html)
- ✅ Reconoce términos técnicos y del proyecto
- ✅ Funciona en español e inglés

---
*Configuración rápida completada - EDF Catalogotablas 2025*
"""

    with open("SPELL_CHECK_QUICK_SETUP.md", "w", encoding="utf-8") as f:
        _ = f.write(instructions)

    print("✅ Instrucciones creadas: SPELL_CHECK_QUICK_SETUP.md")


def main():
    """Función principal"""
    print("⚡ CONFIGURACIÓN RÁPIDA DE SPELL CHECK")
    print("=" * 50)

    # Verificar que estamos en el directorio correcto
    if not Path("pyproject.toml").exists():
        print("❌ Error: No se encontró pyproject.toml")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return 1

    try:
        # Paso 1: Crear configuraciones básicas
        print("\n📋 PASO 1: Creando configuraciones básicas...")
        _ = create_basic_configs()

        # Paso 2: Actualizar pyproject.toml
        print("\n📋 PASO 2: Actualizando pyproject.toml...")
        _ = update_pyproject_toml()

        # Paso 3: Crear instrucciones
        print("\n📋 PASO 3: Creando instrucciones...")
        _ = create_instructions()

        # Paso 4: Resumen
        print("\n📊 RESUMEN:")
        print("  ✅ Configuración de VS Code creada")
        print("  ✅ Configuración de cspell creada")
        print("  ✅ Configuración de PyCharm creada")
        print("  ✅ pyproject.toml actualizado")
        print("  ✅ Instrucciones creadas")

        print("\n🎉 ¡CONFIGURACIÓN RÁPIDA COMPLETADA!")
        print("\n📋 Próximos pasos:")
        print("  1. Instalar extensiones de VS Code")
        print("  2. Instalar cspell: npm install -g cspell")
        print('  3. Probar: cspell "**/*.{md,txt,html}"')

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
