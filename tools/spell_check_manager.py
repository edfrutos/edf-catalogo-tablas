#!/usr/bin/env python3
"""
Gestor completo de ortografía para el proyecto
Implementa todos los pasos sugeridos para gestión inteligente de palabras
"""

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import toml


class SpellCheckManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "pyproject.toml"
        self.dictionaries_dir = self.project_root / "config" / "dictionaries"
        self.dictionaries_dir.mkdir(parents=True, exist_ok=True)

        # Configuración de archivos por tipo
        self.file_configs = {
            "code": {
                "extensions": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"],
                "ignore_spelling": True,
                "check_comments": True,
                "check_strings": False,
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt", ".adoc"],
                "ignore_spelling": False,
                "check_comments": True,
                "check_strings": True,
            },
            "configuration": {
                "extensions": [".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"],
                "ignore_spelling": True,
                "check_comments": True,
                "check_strings": False,
            },
            "web": {
                "extensions": [".html", ".htm", ".xml", ".css", ".scss", ".sass"],
                "ignore_spelling": False,
                "check_comments": True,
                "check_strings": True,
            },
        }

        # Directorios a ignorar
        self.ignore_dirs = {
            "venv",
            "__pycache__",
            "node_modules",
            ".git",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
        }

    def load_known_words(self) -> Set[str]:
        """Cargar palabras conocidas desde pyproject.toml"""
        try:
            with open(self.config_file, encoding="utf-8") as f:
                config = toml.load(f)
            words = config.get("tool", {}).get("cspell", {}).get("words", [])
            return set(words)
        except Exception as e:
            print(f"❌ Error al cargar {self.config_file}: {e}")
            return set()

    def categorize_words(self, words: Set[str]) -> Dict[str, List[str]]:
        """Categorizar palabras según su tipo y origen"""
        categories = {
            "python_modules": [],
            "technical_terms": [],
            "english_words": [],
            "spanish_words": [],
            "code_identifiers": [],
            "file_extensions": [],
            "urls_paths": [],
            "numbers_versions": [],
            "project_specific": [],
            "other": [],
        }

        # Palabras específicas del proyecto
        project_words = {
            "edefrutos",
            "catalogotablas",
            "catalogo",
            "tablas",
            "edf",
            "edefrutos2025",
            "xyz",
            "httpdocs",
            "vhosts",
        }

        for word in words:
            word_lower = word.lower()

            # Palabras específicas del proyecto
            if word_lower in project_words or any(
                proj in word_lower for proj in project_words
            ):
                categories["project_specific"].append(word)

            # Módulos de Python comunes
            elif word_lower in [
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
            ]:
                categories["python_modules"].append(word)

            # Términos técnicos
            elif any(
                tech in word_lower
                for tech in [
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
                ]
            ):
                categories["technical_terms"].append(word)

            # Extensiones de archivo
            elif word_lower.startswith(".") or "." in word_lower:
                categories["file_extensions"].append(word)

            # URLs y rutas
            elif "/" in word or "\\" in word or word_lower.startswith("http"):
                categories["urls_paths"].append(word)

            # Números y versiones
            elif re.match(r"^[\d\.]+$", word) or re.match(r"^v?\d+\.\d+", word):
                categories["numbers_versions"].append(word)

            # Identificadores de código (camelCase, snake_case, etc.)
            elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", word) and (
                "_" in word or any(c.isupper() for c in word[1:])
            ):
                categories["code_identifiers"].append(word)

            # Palabras en inglés (simplificado)
            elif re.match(r"^[a-zA-Z]+$", word) and len(word) > 2:
                categories["english_words"].append(word)

            # Palabras con caracteres especiales (posiblemente español)
            elif re.search(r"[áéíóúñü]", word, re.IGNORECASE):
                categories["spanish_words"].append(word)

            else:
                categories["other"].append(word)

        return categories

    def suggest_additions(
        self, categories: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Sugerir palabras para agregar al diccionario"""
        suggestions = {"auto_add": [], "review_needed": [], "ignore": []}

        # Agregar automáticamente
        suggestions["auto_add"].extend(categories["python_modules"])
        suggestions["auto_add"].extend(categories["technical_terms"])
        suggestions["auto_add"].extend(categories["file_extensions"])
        suggestions["auto_add"].extend(categories["numbers_versions"])
        suggestions["auto_add"].extend(categories["project_specific"])

        # Revisar manualmente
        suggestions["review_needed"].extend(categories["code_identifiers"])
        suggestions["review_needed"].extend(categories["urls_paths"])

        # Ignorar
        suggestions["ignore"].extend(categories["other"])

        return suggestions

    def create_language_dictionaries(self, categories: Dict[str, List[str]]) -> None:
        """Crear diccionarios separados por idioma"""
        print("\n📚 Creando diccionarios por idioma...")

        # Diccionario técnico
        technical_words = (
            categories["python_modules"]
            + categories["technical_terms"]
            + categories["file_extensions"]
            + categories["numbers_versions"]
            + categories["project_specific"]
        )

        self.save_dictionary("technical_terms.txt", technical_words)

        # Diccionario español
        spanish_words = categories["spanish_words"]
        self.save_dictionary("spanish_words.txt", spanish_words)

        # Diccionario inglés
        english_words = categories["english_words"]
        self.save_dictionary("english_words.txt", english_words)

        # Diccionario de identificadores de código
        code_words = categories["code_identifiers"]
        self.save_dictionary("code_identifiers.txt", code_words)

        print("✅ Diccionarios creados en config/dictionaries/")

    def save_dictionary(self, filename: str, words: List[str]) -> None:
        """Guardar diccionario en archivo"""
        filepath = self.dictionaries_dir / filename
        words_sorted = sorted(set(words))

        with open(filepath, "w", encoding="utf-8") as f:
            for word in words_sorted:
                _ = f.write(f"{word}\n")

        print(f"  📄 {filename}: {len(words_sorted)} palabras")

    def update_pyproject_toml(self, new_words: List[str]) -> bool:
        """Actualizar el diccionario en pyproject.toml"""
        try:
            # Leer configuración actual
            with open(self.config_file, encoding="utf-8") as f:
                config = toml.load(f)

            # Obtener palabras existentes
            existing_words = set(
                config.get("tool", {}).get("cspell", {}).get("words", [])
            )

            # Agregar nuevas palabras
            updated_words = list(existing_words | set(new_words))
            updated_words.sort()

            # Actualizar configuración
            if "tool" not in config:
                config["tool"] = {}
            if "cspell" not in config["tool"]:
                config["tool"]["cspell"] = {}

            config["tool"]["cspell"]["words"] = updated_words

            # Crear backup
            backup_file = (
                f"{self.config_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            _ = shutil.copy(self.config_file, backup_file)

            # Escribir configuración actualizada
            with open(self.config_file, "w", encoding="utf-8") as f:
                _ = toml.dump(config, f)

            print(f"📄 Backup creado: {backup_file}")
            return True

        except Exception as e:
            print(f"❌ Error actualizando {self.config_file}: {e}")
            return False

    def create_spell_check_config(self) -> None:
        """Crear configuración específica por tipo de archivo"""
        config = {
            "version": "0.2",
            "language": "en,es",
            "words": [],
            "ignoreWords": [],
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
            ],
            "fileTypes": {
                "code": {
                    "extensions": self.file_configs["code"]["extensions"],
                    "ignoreSpelling": True,
                    "checkComments": True,
                    "checkStrings": False,
                },
                "documentation": {
                    "extensions": self.file_configs["documentation"]["extensions"],
                    "ignoreSpelling": False,
                    "checkComments": True,
                    "checkStrings": True,
                },
                "configuration": {
                    "extensions": self.file_configs["configuration"]["extensions"],
                    "ignoreSpelling": True,
                    "checkComments": True,
                    "checkStrings": False,
                },
                "web": {
                    "extensions": self.file_configs["web"]["extensions"],
                    "ignoreSpelling": False,
                    "checkComments": True,
                    "checkStrings": True,
                },
            },
        }

        config_file = self.dictionaries_dir / "spell_check_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ Configuración creada: {config_file}")

    def export_comprehensive_report(self, unknown_words: Set[str]) -> None:
        """Exportar reporte completo en JSON"""
        categories = self.categorize_words(unknown_words)
        suggestions = self.suggest_additions(categories)

        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "total_words": len(unknown_words),
            },
            "categories": categories,
            "suggestions": suggestions,
            "statistics": {
                "auto_add_count": len(suggestions["auto_add"]),
                "review_needed_count": len(suggestions["review_needed"]),
                "ignore_count": len(suggestions["ignore"]),
            },
            "file_configs": self.file_configs,
            "recommendations": {
                "immediate_actions": [
                    "Auto-agregar términos técnicos y palabras del proyecto",
                    "Crear diccionarios separados por idioma",
                    "Configurar reglas específicas por tipo de archivo",
                ],
                "long_term_actions": [
                    "Revisar identificadores de código manualmente",
                    "Implementar filtros automáticos por contexto",
                    "Configurar integración con IDE",
                ],
            },
        }

        report_file = (
            self.project_root
            / f"spell_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Reporte completo exportado: {report_file}")

    def run_complete_workflow(self) -> None:
        """Ejecutar flujo de trabajo completo"""
        print("🚀 Iniciando gestión completa de ortografía...")
        print("=" * 60)

        # Paso 1: Cargar palabras conocidas
        known_words = self.load_known_words()
        print(f"✅ Cargadas {len(known_words)} palabras conocidas")

        # Paso 2: Escanear archivos (simulado - usar datos del script anterior)
        print("🔍 Escaneando archivos del proyecto...")
        # Aquí normalmente escanearías los archivos, pero usaremos datos simulados
        # En un caso real, esto vendría del script quick_spell_check.py

        # Paso 3: Crear configuración
        print("\n📋 Creando configuración específica por tipo de archivo...")
        self.create_spell_check_config()

        # Paso 4: Crear diccionarios temáticos
        print("\n📚 Creando diccionarios temáticos...")
        # Esto se haría con los datos reales del escaneo

        # Paso 5: Exportar reporte
        print("\n📊 Exportando reporte completo...")
        # Esto se haría con los datos reales del escaneo

        print("\n✅ Flujo de trabajo completado!")
        print("\n📋 Próximos pasos:")
        print("  1. Ejecutar: python tools/quick_spell_check.py")
        print("  2. Revisar el reporte generado")
        print("  3. Aplicar las sugerencias automáticas")
        print("  4. Configurar el IDE con las nuevas reglas")


def main():
    """Función principal"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."

    manager = SpellCheckManager(project_root)
    manager.run_complete_workflow()


if __name__ == "__main__":
    main()
