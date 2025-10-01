#!/usr/bin/env python3
"""
Script para detectar palabras desconocidas y añadirlas automáticamente a pyproject.toml
Uso: python tools/detect_unknown_words.py
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set

import toml


class UnknownWordDetector:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.known_words: Set[str] = set()
        self.unknown_words: Set[str] = set()

    def load_known_words(self) -> None:
        """Cargar palabras conocidas desde pyproject.toml"""
        if not self.pyproject_path.exists():
            print("❌ No se encontró pyproject.toml")
            return

        try:
            with open(self.pyproject_path, encoding="utf-8") as f:
                config = toml.load(f)

            # Obtener palabras de cSpell
            cspell_config = config.get("tool", {}).get("cspell", {})
            words = cspell_config.get("words", [])
            self.known_words = set(words)
            print(f"✅ Cargadas {len(self.known_words)} palabras conocidas")

        except Exception as e:
            print(f"❌ Error al cargar pyproject.toml: {e}")

    def extract_words_from_text(self, text: str) -> Set[str]:
        """Extraer palabras únicas de un texto"""
        # Patrón para palabras (letras, números, guiones bajos, acentos)
        word_pattern = r"\b[a-zA-ZÀ-ÿ\u00C0-\u017F][a-zA-ZÀ-ÿ\u00C0-\u017F0-9_-]*\b"
        words = re.findall(word_pattern, text)

        # Filtrar palabras muy cortas o muy largas
        filtered_words = {word for word in words if len(word) >= 2 and len(word) <= 50}

        return filtered_words

    def scan_file(self, file_path: Path) -> Set[str]:
        """Escanear un archivo en busca de palabras"""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.extract_words_from_text(content)
        except Exception as e:
            print(f"⚠️ Error al leer {file_path}: {e}")
            return set()

    def scan_project(self, extensions: List[str] | None = None) -> Set[str]:
        """Escanear todo el proyecto en busca de palabras"""
        if extensions is None:
            extensions = [".py", ".md", ".html", ".js", ".css", ".txt", ".json"]

        all_words = set()
        scanned_files = 0

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Ignorar directorios comunes
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if any(
                    part in ["venv", "__pycache__", "node_modules", ".git"]
                    for part in file_path.parts
                ):
                    continue

                words = self.scan_file(file_path)
                all_words.update(words)
                scanned_files += 1

                if scanned_files % 100 == 0:
                    print(f"📁 Escaneados {scanned_files} archivos...")

        print(f"✅ Escaneados {scanned_files} archivos")
        return all_words

    def find_unknown_words(self) -> Set[str]:
        """Encontrar palabras desconocidas"""
        print("🔍 Escaneando proyecto en busca de palabras...")
        all_words = self.scan_project()

        # Filtrar palabras conocidas
        unknown = all_words - self.known_words

        # Filtrar palabras comunes en inglés y español
        common_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "unos",
            "unas",
            "y",
            "o",
            "pero",
            "en",
            "con",
            "por",
            "para",
            "de",
            "del",
            "al",
            "se",
            "que",
            "como",
            "this",
            "that",
            "these",
            "those",
            "is",
            "are",
            "was",
            "were",
            "be",
            "este",
            "esta",
            "estos",
            "estas",
            "ese",
            "esa",
            "esos",
            "esas",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "tener",
            "tiene",
            "tenido",
            "hacer",
            "hace",
            "hecho",
            "puede",
            "debe",
        }

        unknown = unknown - common_words

        # Filtrar palabras que parecen ser nombres de archivos o rutas
        unknown = {
            word
            for word in unknown
            if not any(char in word for char in ["/", "\\", "."])
        }

        # Filtrar palabras con caracteres especiales (idiomas eslavos, etc.)
        # Solo mantener palabras con letras básicas del alfabeto latino
        latin_pattern = re.compile(r"^[a-zA-ZÀ-ÿ\u00C0-\u017F0-9_-]+$")
        unknown = {word for word in unknown if latin_pattern.match(word)}

        # Filtrar palabras muy cortas o muy largas
        unknown = {word for word in unknown if 3 <= len(word) <= 30}

        # Filtrar palabras que parecen ser nombres propios o términos técnicos específicos
        # Solo mantener palabras que parecen ser términos del proyecto
        project_terms = {
            word
            for word in unknown
            if any(
                [
                    word.lower().startswith(
                        ("catalog", "tabla", "user", "admin", "app", "data")
                    ),
                    word.lower().endswith(
                        ("tion", "cion", "ment", "mento", "able", "ible")
                    ),
                    word.lower()
                    in [
                        "pip",
                        "flask",
                        "mongodb",
                        "python",
                        "javascript",
                        "html",
                        "css",
                    ],
                ]
            )
        }

        return project_terms

    def add_words_to_config(self, words: Set[str]) -> None:
        """Añadir palabras a la configuración de pyproject.toml"""
        if not words:
            print("✅ No hay palabras nuevas para añadir")
            return

        try:
            with open(self.pyproject_path, encoding="utf-8") as f:
                config = toml.load(f)

            # Obtener configuración actual de cSpell
            if "tool" not in config:
                config["tool"] = {}
            if "cspell" not in config["tool"]:
                config["tool"]["cspell"] = {}
            if "words" not in config["tool"]["cspell"]:
                config["tool"]["cspell"]["words"] = []

            # Añadir nuevas palabras
            current_words = set(config["tool"]["cspell"]["words"])
            new_words = words - current_words

            if new_words:
                config["tool"]["cspell"]["words"].extend(sorted(new_words))

                # Guardar configuración actualizada
                with open(self.pyproject_path, "w", encoding="utf-8") as f:
                    toml.dump(config, f)

                print(f"✅ Añadidas {len(new_words)} palabras nuevas a pyproject.toml:")
                for word in sorted(new_words):
                    print(f"   + {word}")
            else:
                print("✅ Todas las palabras ya están en la configuración")

        except Exception as e:
            print(f"❌ Error al actualizar pyproject.toml: {e}")

    def run(self, auto_add: bool = True) -> None:
        """Ejecutar el detector completo"""
        print("🚀 Iniciando detección de palabras desconocidas...")

        # Cargar palabras conocidas
        self.load_known_words()

        # Encontrar palabras desconocidas
        unknown_words = self.find_unknown_words()

        if unknown_words:
            print(f"\n📝 Encontradas {len(unknown_words)} palabras desconocidas:")
            for word in sorted(unknown_words):
                print(f"   • {word}")

            if auto_add:
                print("\n🔧 Añadiendo palabras a pyproject.toml...")
                self.add_words_to_config(unknown_words)
            else:
                print("\n💡 Para añadir automáticamente, ejecuta con --auto-add")
        else:
            print("✅ No se encontraron palabras desconocidas")


def main():
    parser = argparse.ArgumentParser(
        description="Detectar palabras desconocidas en el proyecto"
    )
    parser.add_argument(
        "--no-auto-add",
        action="store_true",
        help="No añadir automáticamente las palabras encontradas",
    )
    parser.add_argument(
        "--project-root", default=".", help="Directorio raíz del proyecto"
    )

    args = parser.parse_args()

    detector = UnknownWordDetector(args.project_root)
    detector.run(auto_add=not args.no_auto_add)


if __name__ == "__main__":
    main()
