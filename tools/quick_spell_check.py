#!/usr/bin/env python3
"""
Script rápido para verificar palabras desconocidas en archivos específicos
Uso: python tools/quick_spell_check.py [archivo_o_directorio]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

import toml


def load_known_words() -> Set[str]:
    """Cargar palabras conocidas desde pyproject.toml"""
    try:
        with open("pyproject.toml", encoding="utf-8") as f:
            config = toml.load(f)
        words = config.get("tool", {}).get("cspell", {}).get("words", [])
        return set(words)
    except Exception as e:
        print(f"❌ Error al cargar pyproject.toml: {e}")
        return set()


def categorize_words(words: Set[str]) -> Dict[str, List[str]]:
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
        "other": [],
    }

    for word in words:
        word_lower = word.lower()

        # Módulos de Python comunes
        if word_lower in [
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


def suggest_additions(categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Sugerir palabras para agregar al diccionario"""
    suggestions = {"auto_add": [], "review_needed": [], "ignore": []}

    # Agregar automáticamente
    suggestions["auto_add"].extend(categories["python_modules"])
    suggestions["auto_add"].extend(categories["technical_terms"])
    suggestions["auto_add"].extend(categories["file_extensions"])
    suggestions["auto_add"].extend(categories["numbers_versions"])

    # Revisar manualmente
    suggestions["review_needed"].extend(categories["code_identifiers"])
    suggestions["review_needed"].extend(categories["urls_paths"])

    # Ignorar
    suggestions["ignore"].extend(categories["other"])

    return suggestions


def update_dictionary(new_words: List[str], language: str = "en") -> bool:
    """Actualizar el diccionario en pyproject.toml"""
    try:
        # Leer configuración actual
        with open("pyproject.toml", encoding="utf-8") as f:
            config = toml.load(f)

        # Obtener palabras existentes
        existing_words = set(config.get("tool", {}).get("cspell", {}).get("words", []))

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
        import shutil

        _ = shutil.copy("pyproject.toml", "pyproject.toml.backup")

        # Escribir configuración actualizada
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            _ = toml.dump(config, f)

        return True
    except Exception as e:
        print(f"❌ Error actualizando diccionario: {e}")
        return False


def interactive_word_management(unknown_words: Set[str]) -> None:
    """Gestión interactiva de palabras desconocidas"""
    if not unknown_words:
        print("✅ No hay palabras desconocidas para gestionar")
        return

    print(f"\n🔍 Gestión de {len(unknown_words)} palabras desconocidas")
    print("=" * 60)

    # Categorizar palabras
    categories = categorize_words(unknown_words)
    suggestions = suggest_additions(categories)

    # Mostrar estadísticas
    print("\n📊 Categorización de palabras:")
    for category, words in categories.items():
        if words:
            print(f"  {category}: {len(words)} palabras")

    print("\n💡 Sugerencias:")
    print(f"  Auto-agregar: {len(suggestions['auto_add'])} palabras")
    print(f"  Revisar: {len(suggestions['review_needed'])} palabras")
    print(f"  Ignorar: {len(suggestions['ignore'])} palabras")

    # Opciones de gestión
    while True:
        print("\n🛠️  Opciones de gestión:")
        print("  1. Auto-agregar palabras sugeridas al diccionario")
        print("  2. Revisar y seleccionar palabras manualmente")
        print("  3. Ver palabras por categoría")
        print("  4. Exportar palabras a archivo JSON")
        print("  5. Salir sin cambios")

        choice = input("\n🔢 Selecciona una opción: ").strip()

        if choice == "1":
            if suggestions["auto_add"]:
                print(
                    f"\n✅ Agregando {len(suggestions['auto_add'])} palabras automáticamente..."
                )
                if update_dictionary(suggestions["auto_add"]):
                    print("✅ Diccionario actualizado exitosamente")
                    print("📄 Backup creado como: pyproject.toml.backup")
                else:
                    print("❌ Error al actualizar diccionario")
            else:
                print("ℹ️  No hay palabras para agregar automáticamente")

        elif choice == "2":
            manual_word_selection(suggestions["review_needed"])

        elif choice == "3":
            show_words_by_category(categories)

        elif choice == "4":
            export_words_to_json(unknown_words)

        elif choice == "5":
            print("👋 Saliendo sin cambios")
            break

        else:
            print("❌ Opción inválida")


def manual_word_selection(words: List[str]) -> None:
    """Selección manual de palabras"""
    if not words:
        print("ℹ️  No hay palabras para revisar manualmente")
        return

    print(f"\n📝 Revisión manual de {len(words)} palabras")
    print("Comandos: 'add' para agregar, 'skip' para saltar, 'quit' para salir")

    selected_words = []

    for i, word in enumerate(words, 1):
        print(f"\n[{i}/{len(words)}] Palabra: '{word}'")
        action = input("Acción (add/skip/quit): ").strip().lower()

        if action == "add":
            selected_words.append(word)
            print(f"✅ '{word}' agregada")
        elif action == "skip":
            print(f"⏭️  '{word}' saltada")
        elif action == "quit":
            break
        else:
            print("❌ Comando inválido, saltando...")

    if selected_words:
        print(f"\n✅ Agregando {len(selected_words)} palabras seleccionadas...")
        if update_dictionary(selected_words):
            print("✅ Diccionario actualizado exitosamente")
        else:
            print("❌ Error al actualizar diccionario")


def show_words_by_category(categories: Dict[str, List[str]]) -> None:
    """Mostrar palabras por categoría"""
    print("\n📋 Palabras por categoría:")
    print("=" * 60)

    for category, words in categories.items():
        if words:
            print(f"\n🔹 {category.upper()} ({len(words)} palabras):")
            for word in sorted(words)[:10]:  # Mostrar solo las primeras 10
                print(f"  • {word}")
            if len(words) > 10:
                print(f"  ... y {len(words) - 10} más")


def export_words_to_json(words: Set[str]) -> None:
    """Exportar palabras a archivo JSON"""
    categories = categorize_words(words)
    suggestions = suggest_additions(categories)

    export_data = {
        "total_words": len(words),
        "categories": categories,
        "suggestions": suggestions,
        "timestamp": str(Path().cwd()),
    }

    filename = f"spell_check_results_{len(words)}_words.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Resultados exportados a: {filename}")
    except Exception as e:
        print(f"❌ Error exportando resultados: {e}")


def extract_words(text: str) -> Set[str]:
    """Extraer palabras únicas de un texto"""
    word_pattern = r"\b[a-zA-ZÀ-ÿ\u00C0-\u017F][a-zA-ZÀ-ÿ\u00C0-\u017F0-9_-]*\b"
    words = re.findall(word_pattern, text)
    return {word for word in words if 3 <= len(word) <= 30}


def check_file(file_path: Path, known_words: Set[str]) -> Set[str]:
    """Verificar palabras desconocidas en un archivo"""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        words = extract_words(content)
        unknown = words - known_words

        # Filtrar palabras comunes
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

        return unknown - common_words
    except Exception as e:
        print(f"⚠️ Error al leer {file_path}: {e}")
        return set()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    target_path = Path(target)

    print(f"🔍 Verificando palabras desconocidas en: {target_path}")

    known_words = load_known_words()
    print(f"✅ Cargadas {len(known_words)} palabras conocidas")

    unknown_words = set()

    if target_path.is_file():
        # Verificar un archivo específico
        unknown = check_file(target_path, known_words)
        if unknown:
            print(f"\n📝 Palabras desconocidas en {target_path.name}:")
            for word in sorted(unknown):
                print(f"   • {word}")
            unknown_words.update(unknown)
        else:
            print("✅ No se encontraron palabras desconocidas")
    else:
        # Verificar directorio
        extensions = [".py", ".md", ".html", ".js", ".css", ".txt"]
        for file_path in target_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if any(
                    part in ["venv", "__pycache__", "node_modules", ".git"]
                    for part in file_path.parts
                ):
                    continue

                unknown = check_file(file_path, known_words)
                if unknown:
                    unknown_words.update(unknown)

    if unknown_words:
        print(f"\n📊 Total de palabras desconocidas únicas: {len(unknown_words)}")

        # Preguntar si quiere gestionar las palabras
        response = (
            input("\n🤔 ¿Quieres gestionar estas palabras? (s/n): ").strip().lower()
        )
        if response in ["s", "si", "sí", "y", "yes"]:
            interactive_word_management(unknown_words)
    else:
        print("✅ No se encontraron palabras desconocidas")


if __name__ == "__main__":
    main()
