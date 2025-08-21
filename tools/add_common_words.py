#!/usr/bin/env python3
"""
Script para agregar automáticamente palabras comunes del proyecto
a los diccionarios de spell check
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import toml


def load_common_words():
    """Cargar palabras comunes del proyecto"""
    return {
        "project_terms": [
            "edefrutos",
            "catalogotablas",
            "edf",
            "xyz",
            "httpdocs",
            "vhosts",
            "catálogo",
            "catálogos",
            "tablas",
            "catalogos",
        ],
        "spanish_common": [
            "aplicación",
            "aplicaciones",
            "configuración",
            "configurar",
            "configura",
            "documentación",
            "información",
            "instalación",
            "menú",
            "migración",
            "métricas",
            "opción",
            "opciones",
            "permisos",
            "principal",
            "proyecto",
            "reporte",
            "reportes",
            "requeridos",
            "revisa",
            "rápido",
            "scripts",
            "sistema",
            "soporte",
            "también",
            "tests",
            "trabajo",
            "utilidades",
            "utils",
            "variables",
            "ver",
            "verificación",
            "versión",
            "acceder",
            "acceso",
            "archivo",
            "automáticamente",
            "ayuda",
            "completa",
            "costos",
            "desde",
            "diagnóstico",
            "directamente",
            "directo",
            "disponibles",
            "ejecutar",
            "funcionalidades",
            "generados",
            "generan",
            "gestión",
            "imágenes",
            "inicial",
            "integración",
            "interactivo",
            "lanzamiento",
            "mantenimiento",
            "monitoreo",
            "permite",
            "problemas",
            "puedes",
            "raíz",
            "seguir",
            "sobre",
            "todas",
            "usar",
        ],
        "english_common": [
            "access",
            "action",
            "allow",
            "author",
            "help",
            "buckets",
            "configures",
            "configure",
            "query",
            "continuous",
            "data",
            "development",
            "detailed",
            "diagnostic",
            "available",
            "documentation",
            "effect",
            "executes",
            "execute",
            "environment",
            "this",
            "structure",
            "date",
            "flow",
            "generated",
            "tools",
            "individual",
            "initial",
            "installation",
            "interactive",
            "linting",
            "list",
            "menu",
            "migration",
            "migrate",
            "monitor",
            "monitoring",
            "metrics",
            "option",
            "for",
            "permissions",
            "main",
            "project",
            "recommended",
            "reports",
            "required",
            "resource",
            "review",
            "quick",
            "scripts",
            "system",
            "support",
            "statement",
            "also",
            "tests",
            "work",
            "utilities",
            "variables",
            "see",
            "verification",
            "version",
            "access",
            "application",
            "app",
            "file",
            "automatically",
            "bash",
            "complete",
            "costs",
            "from",
            "diagnosis",
            "directly",
            "direct",
            "available",
            "docs",
            "execute",
            "functionalities",
            "generated",
            "generate",
            "management",
            "images",
            "initial",
            "install",
            "integration",
            "interactive",
            "launch",
            "local",
            "maintenance",
            "monitoring",
            "options",
            "allows",
            "pip",
            "main",
            "problems",
            "can",
            "pylint",
            "python3",
            "root",
            "reports",
            "requirements",
            "run_app",
            "quick",
            "script",
            "follow",
            "about",
            "all",
            "tools",
            "your_access_key",
            "your_bucket_name",
            "your_region",
            "your_secret_key",
            "txt",
            "use",
        ],
        "technical_terms": [
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
            "deleteobject",
            "getobject",
            "iam",
            "listallmybuckets",
            "listbucket",
            "putobject",
            "readme",
            "list_buckets",
            "main_app",
            "run_app",
            "python3",
            "com",
            "env",
            "funcionalidades",
            "generan",
            "gestión",
            "imágenes",
            "información",
            "instalación",
            "integración",
            "interactivo",
            "lanzamiento",
            "mantenimiento",
            "menú",
            "migración",
            "migrar",
            "monitorear",
            "monitoreo",
            "métricas",
            "opción",
            "opciones",
            "permisos",
            "permite",
            "pip",
            "principal",
            "problemas",
            "proyecto",
            "puedes",
            "pylint",
            "python3",
            "raíz",
            "reportes",
            "requirements",
            "run_app",
            "rápido",
            "script",
            "scripts",
            "seguir",
            "sobre",
            "tests",
            "todas",
            "tools",
            "tu_access_key",
            "tu_bucket_name",
            "tu_region",
            "tu_secret_key",
            "txt",
            "usar",
            "utilidades",
            "utils",
            "variables",
            "ver",
            "verificación",
            "versión",
        ],
    }


def update_pyproject_toml():
    """Actualizar pyproject.toml con palabras comunes"""
    try:
        # Leer configuración actual
        with open("pyproject.toml", encoding="utf-8") as f:
            config = toml.load(f)

        # Obtener palabras existentes
        existing_words = set(config.get("tool", {}).get("cspell", {}).get("words", []))

        # Cargar palabras comunes
        common_words = load_common_words()
        all_new_words = []

        for _category, words in common_words.items():
            all_new_words.extend(words)

        # Agregar nuevas palabras
        updated_words = list(existing_words | set(all_new_words))
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

        print(
            f"✅ pyproject.toml actualizado con {len(all_new_words)} palabras comunes"
        )
        print(f"📄 Backup creado: {backup_file}")

        # Mostrar estadísticas
        print("\n📊 Estadísticas por categoría:")
        for _category, words in common_words.items():
            print(f"  📝 {_category}: {len(words)} palabras")

        return True

    except Exception as e:
        print(f"❌ Error actualizando pyproject.toml: {e}")
        return False


def update_vscode_settings():
    """Actualizar configuración de VS Code"""
    try:
        vscode_file = Path(".vscode/settings.json")
        if not vscode_file.exists():
            print("❌ Archivo .vscode/settings.json no encontrado")
            return False

        with open(vscode_file, encoding="utf-8") as f:
            settings = json.load(f)

        # Cargar palabras comunes
        common_words = load_common_words()
        all_new_words = []

        for _category, words in common_words.items():
            all_new_words.extend(words)

        # Actualizar palabras en VS Code
        existing_words = set(settings.get("spellright.words", []))
        updated_words = list(existing_words | set(all_new_words))
        updated_words.sort()

        settings["spellright.words"] = updated_words

        # Crear backup
        backup_file = (
            f".vscode/settings.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        _ = shutil.copy(vscode_file, backup_file)

        # Escribir configuración actualizada
        with open(vscode_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        print(
            f"✅ VS Code settings actualizado con {len(all_new_words)} palabras comunes"
        )
        print(f"📄 Backup creado: {backup_file}")

        return True

    except Exception as e:
        print(f"❌ Error actualizando VS Code settings: {e}")
        return False


def update_cspell_config():
    """Actualizar configuración de cspell"""
    try:
        cspell_file = Path("cspell.json")
        if not cspell_file.exists():
            print("❌ Archivo cspell.json no encontrado")
            return False

        with open(cspell_file, encoding="utf-8") as f:
            config = json.load(f)

        # Cargar palabras comunes
        common_words = load_common_words()
        all_new_words = []

        for _category, words in common_words.items():
            all_new_words.extend(words)

        # Actualizar palabras en cspell
        existing_words = set(config.get("words", []))
        updated_words = list(existing_words | set(all_new_words))
        updated_words.sort()

        config["words"] = updated_words

        # Crear backup
        backup_file = f"cspell.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _ = shutil.copy(cspell_file, backup_file)

        # Escribir configuración actualizada
        with open(cspell_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ cspell.json actualizado con {len(all_new_words)} palabras comunes")
        print(f"📄 Backup creado: {backup_file}")

        return True

    except Exception as e:
        print(f"❌ Error actualizando cspell.json: {e}")
        return False


def main():
    """Función principal"""
    print("📚 AGREGANDO PALABRAS COMUNES A DICCIONARIOS")
    print("=" * 50)

    # Verificar que estamos en el directorio correcto
    if not Path("pyproject.toml").exists():
        print("❌ Error: No se encontró pyproject.toml")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return 1

    try:
        # Cargar palabras comunes
        common_words = load_common_words()
        total_words = sum(len(words) for words in common_words.values())

        print(f"\n📋 Palabras a agregar: {total_words}")
        print("📊 Categorías:")
        for category, words in common_words.items():
            print(f"  📝 {category}: {len(words)} palabras")

        # Confirmar acción
        response = (
            input(f"\n🤔 ¿Agregar {total_words} palabras a los diccionarios? (s/n): ")
            .strip()
            .lower()
        )
        if response not in ["s", "si", "sí", "y", "yes"]:
            print("❌ Operación cancelada")
            return 0

        # Actualizar archivos
        print("\n📋 PASO 1: Actualizando pyproject.toml...")
        _ = update_pyproject_toml()

        print("\n📋 PASO 2: Actualizando VS Code settings...")
        _ = update_vscode_settings()

        print("\n📋 PASO 3: Actualizando cspell.json...")
        _ = update_cspell_config()

        print("\n🎉 ¡PALABRAS AGREGADAS EXITOSAMENTE!")
        print("\n📋 Próximos pasos:")
        print("  1. Reiniciar VS Code para aplicar cambios")
        print("  2. Probar: python tools/quick_spell_check.py README.md")
        print("  3. Verificar que las palabras ya no aparecen como desconocidas")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
